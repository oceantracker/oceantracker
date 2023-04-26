# linear interploation for triangles in both space and time
#todo  are BC cords as np.float32, faster as lower memory transfer demand and good enough?
import numpy as np
from scipy.spatial import cKDTree

from oceantracker.interpolator._base_interp import _BaseInterp
from oceantracker.util import basic_util

#  use record dtype to reduce numer of params which must be passed to cell walk
#  requires set up walk_info dtype before importing triangle_interpolator_util,
# as dtype  is used  in a numba signature in triangle_interpolator_util at time of import

from oceantracker.interpolator.util import triangle_interpolator_util ,  eval_interp

from oceantracker.util.parameter_checking import  ParamValueChecker as PVC

# interp info numpy dtype to reduce args passed to numba
#dtype([('f0', '<i4'), ('f1', '<f8', (2, 3))])


class  InterpTriangularNativeGrid_Slayer_and_LSCgrid(_BaseInterp):

    # uses tweaked sci py which allows using start triangle location

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({'bc_walk_tol': PVC(1.0e-5, float,min = 0.),
                                 'max_search_steps': PVC(200,int, min =1)})
        self.grid = {}

    def initial_setup(self):
        super().initial_setup()  # children must call this parent class to default shared_params etc
        params = self.params
        self.code_timer.start('intialize_interplolation_grid')
        si= self.shared_info
        grid = si.classes['reader'].grid
        grid_time_buffers = si.classes['reader'].grid_time_buffers

        # make barcentric transform matrix for the grid,  typee to match numba signature
        grid['bc_transform'] = triangle_interpolator_util.get_BC_transform_matrix(grid['x'].data, grid['triangles'].data).astype(np.float64)

        # build kd tree for initial triangle find node nearest node locations
        #todo delete xy_centriod = np.mean(grid['x'][grid['triangles']], axis=1)
        #todo deleteself.KDtree = cKDTree(xy_centriod)
        self.KDtree = cKDTree(grid['x'])

        self.code_timer.stop('intialize_interplolation_grid')
        # create particle properties to  store history of current triangle  for reuse

        p = si.classes['particle_group_manager']
        p.create_particle_property('manual_update',dict(name='n_cell',  write=False, dtype=np.int32,
                                   initial_value=0))  # start with cell number guess of zero
        p.create_particle_property('manual_update',dict(name='bc_cords',  write=False, initial_value=0., vector_dim=3,dtype=np.float64))

        # BC walk info

        # build cell walk info dtype
        self.walk_counts = np.zeros((5,),dtype=np.int64)
        self.info['walk_info'] = {'particles_killed_after_triangle_walk_retry_failed': 0,'triangle_walks_retried':0}

        if si.hydro_model_is3D:
            # space to record vertical cell for each particles' triangle at two timer steps  for each node in cell containing particle
            # used to do 3D time dependent interpolation
            p.create_particle_property('manual_update',dict(name='nz_cell',  write=False, dtype=np.int32, initial_value=grid_time_buffers['zlevel'].shape[2]-2)) # todo  create  initial serach for vertical cell
            p.create_particle_property('manual_update',dict(name='z_fraction',   write=False, dtype=np.float32, initial_value=0.))
            p.create_particle_property('manual_update', dict(name='z_fraction_bottom_layer', write=False, dtype=np.float32, initial_value=0., description=' thickness of bottom layer in metres, used for log layer velocity interp in bottom layer'))


    def final_setup(self):
        # assign functions to roles
        params = self.params
        si = self.shared_info
        grid = si.classes['reader'].grid
        grid_time_buffers = si.classes['reader'].grid_time_buffers
        part_prop = si.classes['particle_properties']

        self.find_horizontal_cell = triangle_interpolator_util.make_BCwalk_with_move_backs_numba2D(part_prop,grid, grid_time_buffers,
                                    params['bc_walk_tol'],  params['max_search_steps'], si.settings['block_dry_cells'],  si.settings['open_boundary_type'] == 1)

        if si.is_3D_run:
            triangles=  grid['triangles']
            z_level_at_nodes= grid_time_buffers['zlevel']
            nz_with_bottom = grid['bottom_cell_index']


            self.find_vertical_cell = triangle_interpolator_util.make_get_depth_cell_time_varying_Slayer_or_LSCgrid(z_level_at_nodes,
                                                           triangles,   nz_with_bottom,  si.z0)
            pass

    #@profile
    def find_cell(self, xq, nb,step_dt_fraction, active):
        # locate cell in place
        # nt give but not needed in 2D
        si= self.shared_info
        part_prop = si.classes['particle_properties']

        self.code_timer.start('find_horizontal_cell_and_bc_weights')
        self.locate_BCwalk(xq, active)  # best method!
        self.code_timer.stop('find_horizontal_cell_and_bc_weights')

        if si.hydro_model_is3D:
            self.code_timer.start('find_depth_cell')
            n_cell = part_prop['n_cell'].data
            z_fraction = part_prop['z_fraction'].data
            z_fraction_bottom_layer =  part_prop['z_fraction_bottom_layer'].data
            status = part_prop['status'].data
            BCcord     = part_prop['bc_cords'].data
            nz_cell = part_prop['nz_cell'].data

            #xq, nb, step_dt_fraction, status, nz_cell,        z_fraction, z_fraction_bottom_layer, active, walk_counts
            self.find_vertical_cell(xq, n_cell, nb,status, BCcord, nz_cell, z_fraction, z_fraction_bottom_layer, active, self.walk_counts, step_dt_fraction)
            # unpack counts
            wi = self.info['walk_info']
            wi['total_vertical_steps'], wi['longest_vertical_walk'] = self.walk_counts[3:]
            self.code_timer.stop('find_depth_cell')
        pass
    #@profile
    def locate_BCwalk(self,xq, active):
        # Bary Centric walk, flags land triangles in numba code
        si = self.shared_info
        info = self.info
        wi = info['walk_info']

        part_prop = si.classes['particle_properties']
        status=  part_prop['status'].data
        n_cell= part_prop['n_cell'].data
        bc_cords= part_prop['bc_cords'].data

        self.find_horizontal_cell(xq, status, n_cell, bc_cords, active, self.walk_counts)

        # transphere count info
        wi['particles_located_by_walking'],wi['number_of_triangles_walked'],\
                wi['longest_triangle_walk'], wi['nans_encountered_triangle_walk'] = self.walk_counts[:4]

        sel = part_prop['status'].find_subset_where(active, 'eq', si.particle_status_flags['cell_search_failed'], out =self.get_particle_subset_buffer())

        if sel.size > 0:
            self.code_timer.start('kd-tree_retrys')

            wi['triangle_walks_retried'] += sel.size

            new_cell  = self.initial_cell_guess(xq[sel,:])
            part_prop['n_cell'].set_values(new_cell, sel)
            self.find_horizontal_cell(xq, status, n_cell, bc_cords, sel)

            sel = part_prop['status'].find_subset_where(sel, 'eq', si.particle_status_flags['cell_search_failed'], out=self.get_particle_subset_buffer())
            if sel.size > 0:
                wi['particles_killed_after_triangle_walk_retry_failed'] += sel.size # total failed walks
                si.msg_logger.msg('walks too long after kd retry- killed ' + str(sel.shape[0]) + ' particles',warning=True,tabs=0,
                                  hint='Try decreasing time step or increasing interpolator parameter "max_search_steps", current value =' + str(self.params['max_search_steps']))
                # make notes for log file enabling follow up
                si.msg_logger.msg('particle locations of failed walks, first 3 or less ', warning=True,tabs=2)
                si.msg_logger.msg(' location xq =' + str(xq[sel[:3], :].tolist()), warning=True,tabs=2)
                si.msg_logger.msg(' x_old =' + str(part_prop['x_last_good'].data[sel[:3], :].tolist()),warning=True,tabs=2)
                # kill particles
                part_prop['status'].set_values(si.particle_status_flags['dead'], sel)
            self.code_timer.stop('kd-tree_retrys')


    def initial_cell_guess(self, xq):
        # find nearest cell
        si=self.shared_info
        grid = si.classes['reader'].grid
        grid_time_buffers = si.classes['reader'].grid_time_buffers

         # find nearest node
        dist, nodes = self.KDtree.query(xq[:, :2])
        nodes = nodes.astype(np.int32)  # KD tre gives in644need for compatibility of types

        # look in triangles attached to each node for tri containing the point
        n_cell= triangle_interpolator_util.check_if_point_inside_triangle_connected_to_node(xq, nodes,
                                     grid['node_to_tri_map'], grid['tri_per_node'],  grid['bc_transform'], self.params['bc_walk_tol'])
        # if x is nan dist is infinite
        n_cell[~np.isfinite(dist)] = -1

        return n_cell

    def are_points_inside_domain(self, xq):
        n_cell  = self.initial_cell_guess(xq)
        bc = self.get_bc_cords(xq,n_cell)
        is_inside=  np.all(np.logical_and(bc >= -self.params['bc_walk_tol'], bc  <= 1.+self.params['bc_walk_tol']),axis=1)
        return is_inside, n_cell  # is inside if  magnitude of all BC < 1


    def eval_field_interpolation_at_particle_locations(self, fieldObj, nb  , output, active, step_dt_fraction=None):
        # in place evaluation of field interpolation
        si = self.shared_info
        grid = si.classes['reader'].grid
        part_prop= si.classes['particle_properties']
        n_cell   = part_prop['n_cell'].data
        bc_cords = part_prop['bc_cords'].data

        if fieldObj.is_time_varying():
            if fieldObj.is3D():
                nz_cell = part_prop['nz_cell'].data
                nz_bottom = grid['bottom_cell_index']
                z_fraction = part_prop['z_fraction'].data

                if fieldObj.params['name']=='water_velocity':
                    # 3D vel needs log layer interp in bottom cell
                    z_fraction_bottom_layer = part_prop['z_fraction_bottom_layer'].data

                    eval_interp.eval_water_velocity_3D(basic_util.atLeast_Nby1(output),
                                                       fieldObj.data,
                                                       nb,
                                                       step_dt_fraction,
                                                       grid['triangles'],
                                                       n_cell,
                                                       nz_cell,
                                                       nz_bottom,
                                                       z_fraction,
                                                    z_fraction_bottom_layer,
                                                       bc_cords,     active)
                else:
                    eval_interp.time_dependent_3Dfield(basic_util.atLeast_Nby1(output),
                                                       fieldObj.data,
                                                       nb,
                                                       step_dt_fraction,
                                                       grid['triangles'],
                                                       n_cell, nz_cell,nz_bottom,
                                                       z_fraction, bc_cords, active)
                    #F_out, F_data, nb, step_dt_fraction, tri, nz_bottom, n_cell, nz_cell, z_fraction, BCcord, active
            else:
                eval_interp.time_dependent_2Dfield(basic_util.atLeast_Nby1(output),
                                                   fieldObj.data,
                                                   nb,
                                                   step_dt_fraction,
                                                   grid['triangles'],
                                                   n_cell,
                                                   bc_cords, active)
        else:
            # 2D or 3D non-time varying
            if fieldObj.is3D():
                # todo eval_interp3D_timeIndependent not implented for 3D non-time varying fields
                nz_cell = part_prop['nz_cell'].data
                z_fraction_nodes = part_prop['z_fraction_nodes'].data
                raise Exception('eval_field_interpolation_at_particle_locations : spatial interp using eval_interp3D_timeIndependent not implemented yet ')
            else:
                eval_interp.time_independent_2Dfield(basic_util.atLeast_Nby1(output),
                                                     fieldObj.data,
                                                     grid['triangles'],
                                                     n_cell,
                                                     bc_cords, active)

    def eval_field_interpolation_at_given_locations(self, fieldObj,x, time=None,  output=None, n_cell= None):
        # in  evaluation of field interpolation at specific locations, ie not particle locations
        #todo not working - eval_field_interpolation_at_given_locations

        si = self.shared_info
        grid = si.classes['reader'].grid
        grid_time_buffers = si.classes['reader'].grid_time_buffers
        part_prop= si.classes['particle_properties']
        reader = si.classes['reader']

        # is no output name give particle property for output is same as hindcast fieldName
        if output is None:
            if  fieldObj.data.shape[3]> 1:
                output= np.full((x.shape[0], fieldObj.data.shape[3]), np.nan)
            else:
                output = np.full((x.shape[0],),np.nan)

        if n_cell is None:
            n_cell= self.initial_cell_guess(x)

        # get bc cords for the cells
        bc_cords = self.get_bc_cords(x, n_cell)
        active = np.arange(x.shape[0])

        if fieldObj.is_time_varying():
            # get buffer time step and time fraction
            nt = reader.time_to_hydro_model_index(time)
            nb = reader.buffer_index_to_buffer_offset(nt)
            step_dt_fraction = abs(time - reader.get_particle_time(nb)) / si.hydo_model_time_step

            if fieldObj.is3D():
                z_fraction_nodes = part_prop['z_fraction_nodes'].data
                nz_nodes = part_prop['nz_cell'].data

                if fieldObj.params['name']=='water_velocity':
                    # 3D vel needs log layer interp in bottom cell
                    eval_interp.eval_water_velocity_3D(basic_util.atLeast_Nby1(output),
                                                       fieldObj.data,
                                                       nb,
                                                       step_dt_fraction,
                                                       grid['triangles'],
                                                       n_cell,
                                                       nz_nodes, z_fraction_nodes, bc_cords,
                                                       grid_time_buffers['zlevel'], grid['bottom_cell_index'],
                                                       active)
                else:
                    eval_interp.time_dependent_3Dfield(basic_util.atLeast_Nby1(output),
                                                       fieldObj.get_data(nt_buffer=nb),
                                                       fieldObj.get_data(nt_buffer=nb + 1),
                                                       step_dt_fraction,
                                                       grid['triangles'],
                                                       n_cell,
                                                       nz_nodes, z_fraction_nodes, bc_cords, active)
            else:
                # todo 2D time dep not not working yet
                eval_interp.time_dependent_2Dfield(basic_util.atLeast_Nby1(output),
                                                   fieldObj.data,
                                                   nb,
                                                   step_dt_fraction,
                                                   grid['triangles'],
                                                   n_cell,
                                                   bc_cords, active)
        else:
            # 2D or 3D non-time varying
            if fieldObj.is3D():
                # todo eval_interp3D_timeIndependent not implemented for 3D non-time varying fields
                nz_nodes = part_prop['nz_cell'].data
                z_fraction_nodes = part_prop['z_fraction_nodes'].data
                raise Exception('eval_field_interpolation_at_given_locations: spatial interp using eval_interp3D_timeIndependent not implemented yet ')
            else:
                # is working
                eval_interp.time_independent_2Dfield(basic_util.atLeast_Nby1(output),
                                                     fieldObj.data,
                                                     grid['triangles'],
                                                     n_cell,
                                                     bc_cords, active)
                return  output


    def get_bc_cords(self,x,n_cells):
        si= self.shared_info
        grid = si.classes['reader'].grid
        bc_cords = np.full((x.shape[0],3), 0.)
        triangle_interpolator_util.get_BC_cords_numba(x, n_cells, grid['bc_transform'], bc_cords)
        return bc_cords

    def close(self):
        si=self.shared_info
        info = self.info

        # transfer walk stats to class info to write  in case_info file

        wi = info['walk_info']
        wi['average_number_of_triangles_walked']= wi['number_of_triangles_walked']/max(1,wi['particles_located_by_walking'])
        if si.is_3D_run:
            wi['average_vertical_walk_steps'] = wi['total_vertical_steps'] / max(1, wi['particles_located_by_walking'])

        if wi['particles_killed_after_triangle_walk_retry_failed'] > 0:
            si.msg_logger.msg(f" Of {wi['particles_located_by_walking']:3d} particles located {wi['particles_killed_after_triangle_walk_retry_failed']:3d}, failed to find cell",
                              crumbs='Interpolator cals, InterpTriangularNativeGrid_Slayer_and_LSCgrid',
                              hint= f"Try increasing interpolator parameter 'max_search_steps', current value ={self.params['max_search_steps']:3d}")

# Below is numpy version of numba BC cord code, now only used as check
#________________________________________________
    def get_cell_cords_check(self,x,n_cell):
        # barycentric cords, only for use with non-improved scipy and KDtree for al time steps
        # numba code does this faster
        si = self.shared_info
        grid = si.classes['reader'].grid

        TT = np.take(grid['bc_transform'], n_cell, axis=0,)
        b = np.full((x.shape[0],3), np.nan, order='C')
        b[:,:2] = np.einsum('ijk,ik->ij', TT[:, :2], x[:, :2] - TT[:, 2], order='C')  # Einstein summation
        b[:,2] = 1. - b[:,:2].sum(axis=1)
        return b




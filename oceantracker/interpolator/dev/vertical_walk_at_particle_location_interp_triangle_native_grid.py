# linear interploation for triangles in both space and time

#todo  are BC cords as np.float32, faster as lower memory transfer demand and good enough?
import numpy as np

from scipy.spatial import cKDTree

from oceantracker.interpolator._base_interp import _BaseInterp
from oceantracker.util import basic_util

# import dev versions of eval and walk
from oceantracker.interpolator.util.dev import vertical_walk_at_particle_location_triangle_interpolator_util as triangle_interpolator_util
from oceantracker.interpolator.util.dev import vertical_walk_at_particle_location_eval_interp as eval_interp

from oceantracker.util.parameter_checking import  ParamDictValueChecker as PVC

class  InterpTriangularNativeGrid_Slayer_and_LSCgrid(_BaseInterp):

    # uses tweaked sci py which allows using start triangle location

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({'bc_walk_tol': PVC(1.0e-6, float,min = 0.), 'max_search_steps': PVC(100,int, min =1)})
        self.grid = {}

    def initialize(self):
        super().initialize()  # children must call this parent class to default shared_params etc

        self.code_timer.start('intialize_interplolation_grid')
        si= self.shared_info
        self.build_grid()
        grid = si.classes['reader'].grid
        # build kd tree for initial triangle find of particle initial locations
        xy_centriod = np.mean(grid['x'][grid['triangles']], axis=1)
        self.KDtree = cKDTree(xy_centriod)

        self.code_timer.stop('intialize_interplolation_grid')
        # create particle properties to  store history of current triangle  for reuse

        p = si.classes['particle_group_manager']
        p.create_particle_property('manual_update',dict(name='n_cell',  write=False, dtype=np.int32,
                                   initial_value=0))  # start with cell number guess of zero
        p.create_particle_property('manual_update',dict(name='bc_cords',  write=False, initial_value=0., vector_dim=3))

        # BC walk stats
        info = self.info
        self.walk_stats = np.zeros((2,),dtype=triangle_interpolator_util.walk_stats)


        if si.hindcast_is3D:
            # space to record vertical cell for each particles' triangle at two timer steps  for each node in cell containing particle
            # used to do 3D time dependent interpolation
            p.create_particle_property('manual_update',dict(name='nz_cell',  write=False, dtype=np.int32, initial_value=grid['zlevel'].shape[2]-2)) # todo  create  initial serach for vertical cell
            p.create_particle_property('manual_update', dict(name='nz_nodes', write=False, dtype=np.int32, initial_value=0, vector_dim=2,prop_dim3=3,description='z nodes for levels above and below particle, used to get reference used in field interpolation'))
            p.create_particle_property('manual_update', dict(name='bottom_layer_thickness', write=False, dtype=np.float32, initial_value=0.,description=' thickness of bottom layer in metres, used for log layer velocity interp in bottom layer'))
            p.create_particle_property('manual_update',dict(name='z_fraction',   write=False, dtype=np.float32, initial_value=0.))

    def build_grid(self):
        si = self.shared_info
        grid = si.classes['reader'].grid
        # build transformation matrix to calculate bc cords in same form as scipy qhulll
        grid['bc_transform'] = triangle_interpolator_util.get_BC_transform_matrix(grid['x'].data, grid['triangles'].data)


    def find_cell(self, xq, nb,step_dt_fraction, active):
        # locate cell in place
        # nt give but not needed in 2D
        si= self.shared_info
        self.code_timer.start('find_cells_and_weights')

        self.locate_BCwalk(xq, nb,step_dt_fraction, active)  # best method!
        self.code_timer.stop('find_cells_and_weights')

        if si.hindcast_is3D:
            self.code_timer.start('find_depth_cell')
            # insert depth cells and fractions
            self.get_depth_cell(xq, nb, step_dt_fraction, active)

            #print('vcell', self.info['n_total_vertical_search_steps'] / active.shape[0])
            self.code_timer.stop('find_depth_cell')

    def locate_BCwalk(self,xq, nb,step_dt_fraction, active):
        # Bary Centric walk, flags land triangles in numba code
        si = self.shared_info
        grid = si.classes['reader'].grid
        part_prop = si.classes['particle_properties']

        triangle_interpolator_util.BCwalk_with_move_backs_numba2D(
                                                xq,
                                                part_prop['x_last_good'].data,
                                                part_prop['status'].data,

                                                part_prop['bc_cords'].data,
                                                grid['bc_transform'],
                                                grid['adjacency'],
                                                grid['dry_cell_index'],
                                                si.run_params['block_dry_cells'],
                                                self.params['bc_walk_tol'],
                                                self.params['max_search_steps'],
                                                si.case_params['run_params']['open_boundary_type'] == 1,
                                                active,self.walk_stats[0],  part_prop['n_cell'].data)
        sel = part_prop['status'].find_subset_where(active, 'eq', si.particle_status_flags['cell_search_failed'], out =self.get_particle_subset_buffer())

        if sel.shape[0] > 0:
            self.code_timer.start('kd-tree_retrys')
            new_cell, status, bc = self.initial_cell_guess(xq[sel,:2])
            part_prop['n_cell'].set_values(new_cell, sel)
            triangle_interpolator_util.BCwalk_with_move_backs_numba2D(
                                        xq,
                                        part_prop['x_last_good'].data,
                                        part_prop['status'].data,

                                        part_prop['bc_cords'].data,
                                        grid['bc_transform'],
                                        grid['adjacency'],
                                        grid['dry_cell_index'],
                                        si.run_params['block_dry_cells'],
                                        self.params['bc_walk_tol'],
                                        self.params['max_search_steps'],
                                        si.case_params['run_params']['open_boundary_type'] == 1,
                                        sel,    self.walk_stats[0],part_prop['n_cell'].data)

            sel = part_prop['status'].find_subset_where(sel, 'eq', si.particle_status_flags['cell_search_failed'], out=self.get_particle_subset_buffer())
            if sel.shape[0] > 0:
                si.case_log.write_warning('Some BC walks too long after kd retry- killed ' + str(sel.shape[0]) + ' particles')
                self.info['failed_searches'] += sel.shape[0]
                # make notes for log file enabling follow up
                si.case_log.write_warning('failed BCwalks_after_KDtree_retry, particles' + str(sel.tolist()) + ' xq =' + str(xq[sel, :].tolist()))
                # kill particles
                part_prop['status'].set_values(si.particle_status_flags['dead'], sel)
            self.code_timer.stop('kd-tree_retrys')


    def initial_cell_guess(self, xq):
        # find nearest cell
        si=self.shared_info
        grid = si.classes['reader'].grid
        dist, n_cell = self.KDtree.query(xq[:, :2])

        n_cell = n_cell.astype(np.int32)  # KD tre gives in64need for compartibilty of types

        n_cell[np.any(~np.isfinite(xq), axis=1)] = -1 # stops walking for non-finite initial cords

        # KD tree is not perfect as finds nearest centriod, so do a walk to correct
        status  = np.full((xq.shape[0],),10, dtype=np.int32)
        bc      = np.full((xq.shape[0],3),  0., dtype=np.float64)
        triangle_interpolator_util.BCwalk_with_move_backs_numba2D(
            xq,
            xq,# use xq for last good
            status,

            bc,
            grid['bc_transform'],
            grid['adjacency'],
            grid['dry_cell_index'],
            False,  # dont block dry cells, just block at domain boundary
            self.params['bc_walk_tol'],
            self.params['max_search_steps'],
            False, # no open boundary, as must start inside
            np.arange(xq.shape[0]), self.walk_stats[0], n_cell)

        return n_cell

    def are_points_inside_domain(self, xq):
        n_cell  = self.initial_cell_guess(xq)
        bc = self.get_bc_cords(xq,n_cell)
        is_inside=  np.all(np.logical_and(bc >= -self.params['bc_walk_tol'], bc  <= 1.+self.params['bc_walk_tol']),axis=1)
        return is_inside, n_cell  # is inside if  magitude of all BC < 1

    def eval_field_interpolation_at_particle_locations(self, fieldObj, nb  , output, active, step_dt_fraction=None):
        # in place evaluation of field interpolation
        si = self.shared_info
        grid = si.classes['reader'].grid
        part_prop= si.classes['particle_properties']
        n_cell   = part_prop['n_cell'].data
        nz_nodes = part_prop['nz_nodes'].data
        bc_cords = part_prop['bc_cords'].data

        if fieldObj.is_time_varying():
            if fieldObj.is3D():
                nz_cell = part_prop['nz_cell'].data
                z_fraction = part_prop['z_fraction'].data

                if fieldObj.params['name']=='water_velocity':
                    # 3D vel needs log layer interp in bottom cell
                    bottom_layer_thickness = part_prop['bottom_layer_thickness'].data
                    eval_interp.eval_water_velocity_3D(basic_util.atLeast_Nby1(output),
                                                       fieldObj.data,
                                                       nb,
                                                       step_dt_fraction,
                                                       grid['triangles'],
                                                       n_cell,
                                                       nz_cell,nz_nodes, z_fraction,bottom_layer_thickness, bc_cords,
                                                       si.z0,   active)
                else:
                    eval_interp.time_dependent_3Dfield(basic_util.atLeast_Nby1(output),
                                                       fieldObj.data,
                                                       nb,
                                                       step_dt_fraction,
                                                       grid['triangles'],
                                                       n_cell,nz_nodes,
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
            nt = reader.time_to_global_time_step(time)
            nb = reader.global_index_to_buffer_index(nt)
            step_dt_fraction = abs(time - reader.get_particle_time(nb)) / si.hindcast_time_step

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
                                                       grid['zlevel'], grid['bottom_cell_index'], si.z0,
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

    def get_depth_cell(self, xq, nb, step_dt_fraction,active):
        # find depth cell number starting with a guess of previous depth cell
        # for fixed fractional depth grid
        si = self.shared_info
        grid = si.classes['reader'].grid
        part_prop = si.classes['particle_properties']

        zlevel_nodes= grid['zlevel']
        nz_bottom = grid['bottom_cell_index']
        n_cell      = part_prop['n_cell'].data
        nz_cell    = part_prop['nz_cell'].data
        status      = part_prop['status'].data
        BCcords     = part_prop['bc_cords'].data
        z_fraction = part_prop['z_fraction'].data
        bottom_layer_thickness =  part_prop['bottom_layer_thickness'].data
        nz_nodes = part_prop['nz_nodes'].data

        triangle_interpolator_util.get_depth_cell_time_varying_Slayer_or_LSCgrid(
                                            xq[:, 2], nb, step_dt_fraction, zlevel_nodes, grid['triangles'], n_cell,
                                            nz_bottom, BCcords, status,
                                            nz_cell,nz_nodes, z_fraction,bottom_layer_thickness, si.z0, active,
                                            self.walk_stats[1])
        info = self.info


    def get_bc_cords(self,x,n_cells):
        si= self.shared_info
        grid = si.classes['reader'].grid
        bc_cords = np.full((x.shape[0],3), 0.)
        triangle_interpolator_util.get_BC_cords_numba(x, n_cells, grid['bc_transform'], bc_cords)
        return bc_cords

    def close(self):
        si=self.shared_info
        info = self.info
        # guard against no particle tracking done, eg all points outside domain so zero active

        # note walk statistics

        info['bc_walk'] ={}
        for name in self.walk_stats[0].dtype.names:
            info['bc_walk'][name]= self.walk_stats[0][name]
        info['bc_walk']['average_number_of_triangles_walked'] =  info['bc_walk']['total_steps'] /  max(info['bc_walk']['particles_located'], 1)

        # there are vertical walk stats
        if si.hindcast_is3D:
            info['vertical_walk'] = {}
            for name in self.walk_stats[1].dtype.names:
                info['vertical_walk'][name] = self.walk_stats[1][name]

            info['vertical_walk']['average_number_of_triangles_walked'] =  info['vertical_walk']['total_steps'] /  max(info['vertical_walk']['particles_located'], 1)


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




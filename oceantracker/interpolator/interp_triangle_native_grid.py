# linear interploation for triangles in both space and time
#todo  are BC cords as np.float32, faster as lower memory transfer demand and good enough?
import numpy as np
from scipy.spatial import cKDTree

from oceantracker.interpolator._base_interp import _BaseInterp
from oceantracker.util import basic_util
from oceantracker.util.profiling_util import function_profiler
from time import perf_counter
from oceantracker.util import numba_util
from oceantracker.util import numpy_util
from numba import typeof, types as nbt, from_dtype

from oceantracker.interpolator.util import triangle_interpolator_util as tri_interp_util ,  eval_interp

from oceantracker.util.parameter_checking import  ParamValueChecker as PVC


class  InterpTriangularNativeGrid_Slayer_and_LSCgrid(_BaseInterp):

    # uses tweaked sci py which allows using start triangle location

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({'bc_walk_tol': PVC(1.0e-5, float,min = 0.),
                                 'max_search_steps': PVC(500,int, min =1)})
        self.grid = {} #todo get rid?
        self.info['current_buffer_index'] = np.zeros((2,), dtype=np.int32)

    #@function_profiler(__name__)
    def initial_setup(self):
        super().initial_setup()  # children must call this parent class to default shared_params etc
        params = self.params
        si= self.shared_info
        grid = si.classes['reader'].grid

        # make barcentric transform matrix for the grid,  typee to match numba signature
        t0 = perf_counter()
        grid['bc_transform'] = tri_interp_util.get_BC_transform_matrix(grid['x'].data, grid['triangles'].data).astype(np.float64)
        si.msg_logger.progress_marker('built barycentric-transform matrix', start_time=t0)
        # build kd tree for initial triangle find node nearest node locations
        #todo delete xy_centriod = np.mean(grid['x'][grid['triangles']], axis=1)
        #todo deleteself.KDtree = cKDTree(xy_centriod)
        self.KDtree = cKDTree(grid['x'])

        # create particle properties to  store history of current triangle  for reuse

        p = si.classes['particle_group_manager']
        p.create_particle_property('manual_update',dict(name='n_cell',  write=False, dtype=np.int32,
                                   initial_value=0))  # start with cell number guess of zero
        p.create_particle_property('manual_update',dict(name='bc_cords',  write=False, initial_value=0., vector_dim=3,dtype=np.float64))

        # BC walk info
        if si.hydro_model_is3D:
            # space to record vertical cell for each particles' triangle at two timer steps  for each node in cell containing particle
            # used to do 3D time dependent interpolation
            p.create_particle_property('manual_update',dict(name='nz_cell',  write=False, dtype=np.int32, initial_value=grid['zlevel'].shape[2]-2)) # todo  create  initial serach for vertical cell
            p.create_particle_property('manual_update',dict(name='z_fraction',   write=False, dtype=np.float32, initial_value=0.))
            p.create_particle_property('manual_update', dict(name='z_fraction_bottom_layer', write=False, dtype=np.float32, initial_value=0., description=' thickness of bottom layer in metres, used for log layer velocity interp in bottom layer'))

        # set up place for walk info failures
        self.info['walk_info'] = {'walk_failures': {'retries': [],'full_failures':[]}}

        # attach a reader to this interpolator
        self.reader = si.classes['reader']

    def final_setup(self):

        # set up a grid class,part_prop and vertical cell find functions to minimise numba function arguments
        si = self.shared_info
        reader = self.reader
        grid = reader.grid
        fi = reader.info['file_info']
        bi = reader.info['buffer_info']

        #todo z0, move this where grid is built?
        grid['z0'] = si.case_runner_params['settings']['z0']

        self.grid_as_struct = numpy_util.numpy_structure_from_dict(grid)

        # build cell walk info
        step_info = dict( is_3D_run = si.is_3D_run,
                        max_triangle_walk_steps =  self.params[ 'max_search_steps'],
                        open_boundary_type= si.settings['open_boundary_type'],
                        block_dry_cells=si.settings['block_dry_cells'],
                        bc_walk_tol=self.params[ 'bc_walk_tol'],
                        particles_located_by_walking=0,
                        number_of_triangles_walked=0,
                        longest_triangle_walk= 0,
                        nans_encountered_triangle_walk=0,
                        triangle_walks_retried=0,
                        particles_killed_after_triangle_walk_retry_failed=0,
                        total_vertical_steps_walked=0,
                        longest_vertical_walk=0,
                        nb = np.zeros((2,),dtype=np.int32),
                        fractional_time_steps=np.zeros((2,),dtype=np.float64),
                        # information needed to work out location in reader buffer
                        hindcast_first_time=fi['first_time'],
                        hindcast_last_time=fi['last_time'],
                        n_time_steps_in_hindcast= fi['n_time_steps_in_hindcast'],
                        time_buffer_size =  bi['buffer_size'],
                        model_direction= int(si.model_direction),
                        current_hydro_model_step= 0,
                        hydro_model_time_step =reader.info['hydro_model_time_step']
                        )
        self.step_info= numpy_util.numpy_structure_from_dict(step_info) # class to use inside numba functions

        # point at particle prop block
        part_prop_as_structure = si.classes['particle_group_manager'].part_prop_as_struct

        # types for signatures
        part_prop_type = typeof(part_prop_as_structure)
        grid_type= typeof(self.grid_as_struct)
        step_info_type = typeof(self.step_info)
        x_type = typeof(part_prop_as_structure['x'])

        # same signature for both walk functions
        sig_walk = [x_type,grid_type , part_prop_type, nbt.int32[:],step_info_type ]

        # define walk function, water velocity eval interpolator function
        sig_vel = [x_type, nbt.float32[:, :, :, :], grid_type, part_prop_type, nbt.int32[:], step_info_type]
        if si.is_3D_run:
            self.walk_function = numba_util.njitter(tri_interp_util.combined_cell_and_depth_walk, sig_walk)

        else:
            self.walk_function = numba_util.njitter(tri_interp_util.BCwalk_with_move_backs,
                                                            sig_walk, parallel=False)
        pass

        #todo put 2d vel eval value here to as??

    def setup_interp_time_step(self, time_sec, xq, active):
        # set up stuff needed by all fields before any 2D interpolation
        # eg query point and nt the current global time step, from which we are making nt+1
        info = self.info
        reader = self.reader
        grid = reader.grid
        st = self.step_info

        # set buffer index from this time and next inside stepinfo
        tri_interp_util.set_hindcast_buffer_steps(time_sec,st)

        time_hindcast = grid['time'][st['nb'][0]]
        tri_interp_util.set_time_fractions(time_sec, time_hindcast, st)

        # find cell for xq, node list and weight for interp at calls
        self.find_cell(xq, active)

    def check_steps_in_reader_buffer(self,time_sec):
        if not self.reader.are_time_steps_in_buffer(time_sec):
            self.reader.fill_time_buffer(time_sec)  # get next steps into buffer if not in buffer

    #@function_profiler(__name__)
    def interp_field_at_current_particle_locations(self, field_instance, active, output):
        # interp reader fieldName inplace to particle locations to same time and memory
        # output can optionally be redirected to another particle property name different from  reader's fieldName
        # particle_prop_name
       # in place evaluation of field interpolation
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        part_prop_struct = si.classes['particle_group_manager'].part_prop_as_struct
        grid_struct = self.grid_as_struct
        st = self.step_info

        # args the same for all
        args = (basic_util.atLeast_Nby1(output),
                field_instance.data, grid_struct,
                part_prop_struct,
                active, st)

        if field_instance.is_time_varying():
            if field_instance.is3D():
                if field_instance.params['name'] == 'water_velocity':
                    # 3D vel needs log layer interp in bottom cell
                    eval_interp.eval_water_velocity_3D(*args)
                else:
                    eval_interp.time_dependent_3Dfield(*args)
                    # F_out, F_data, nb, fractional_time_step, tri, nz_bottom, n_cell, nz_cell, z_fraction, BCcord, active
            else:
                eval_interp.time_dependent_2Dfield(*args)
        else:
            # 2D or 3D non-time varying
            if field_instance.is3D():
                # todo eval_interp3D_timeIndependent not implented for 3D non-time varying fields
                raise Exception('eval_field_interpolation_at_particle_locations : spatial interp using eval_interp3D_timeIndependent not implemented yet ')
            else:
                eval_interp.time_independent_2Dfield(*args)

    #@function_profiler(__name__)
    def interp_named_field_at_given_locations_and_time(self, fieldName, x, time=None, n_cell=None, output=None):
        # interp reader fieldName at specfied locations,  not particle locations
        # output can optionally be redirected to another particle property name different from  reader's fieldName
        # particle_prop_name
        #todo not working or used
        si = self.shared_info
        output = si.classes['interpolator'].eval_field_interpolation_at_given_locations(si.classes['fields'][fieldName], x, time, output=output, n_cell=n_cell)

        return output

    def find_cell(self, xq, active):
        # locate cell in place
        # nt give but not needed in 2D
        si= self.shared_info
        info = self.info
        wi = info['walk_info']
        part_prop_struct = si.classes['particle_group_manager'].part_prop_as_struct
        grid_struct= self.grid_as_struct
        st = self.step_info

        # used 2D or 3D walk chosen above
        self.walk_function(xq, grid_struct, part_prop_struct, active, st)

        #retry any too long wallks
        part_prop = si.classes['particle_properties']

        sel = part_prop['status'].find_subset_where(active, 'eq', si.particle_status_flags['cell_search_failed'], out =self.get_particle_subset_buffer())
        if sel.size > 0:
            wf = {'x0':part_prop['x_last_good'].get_values(sel),
                  'xq':part_prop['x'].get_values(sel) }
            wi['walk_failures']['retries'].append(wf)

            st['triangle_walks_retried'] += sel.size
            new_cell  = self.initial_cell_guess(xq[sel,:])
            part_prop['n_cell'].set_values(new_cell, sel)
            self.horizontal_walk_func(xq,grid_struct, part_prop_struct, sel, st)

            # recheck for additional failures
            sel = part_prop['status'].find_subset_where(sel, 'eq', si.particle_status_flags['cell_search_failed'], out=self.get_particle_subset_buffer())
            if sel.size > 0:
                wf = {'x0': part_prop['x_last_good'].get_values(sel),
                      'xq': part_prop['x'].get_values(sel)}

                wi['walk_failures']['full_failures'].append(wf)
                st['particles_killed_after_triangle_walk_retry_failed'] += sel.size # total failed walks
                si.msg_logger.msg('walks too long after kd retry- killed ' + str(sel.shape[0]) + ' particles',warning=True,tabs=0,
                                  hint='Try decreasing time step or increasing interpolator parameter "max_search_steps", current value =' + str(self.params['max_search_steps']))
                # make notes for log file enabling follow up
                si.msg_logger.msg('particle locations of failed walks, first 3 or less ', warning=True,tabs=2)
                si.msg_logger.msg(' location xq =' + str(xq[sel[:3], :].tolist()), warning=True,tabs=2)
                si.msg_logger.msg(' x_old =' + str(part_prop['x_last_good'].data[sel[:3], :].tolist()),warning=True,tabs=2)
                # kill particles
                part_prop['status'].set_values(si.particle_status_flags['dead'], sel)

    #@function_profiler(__name__)
    def initial_cell_guess(self, xq):
        # find nearest cell
        si=self.shared_info
        grid = si.classes['reader'].grid

         # find nearest node
        dist, nodes = self.KDtree.query(xq[:, :2])
        nodes = nodes.astype(np.int32)  # KD tree gives int64,need for compatibility of types

        # look in triangles attached to each node for tri containing the point
        n_cell= tri_interp_util.check_if_point_inside_triangle_connected_to_node(xq, nodes,
                                     grid['node_to_tri_map'], grid['tri_per_node'],  grid['bc_transform'], self.params['bc_walk_tol'])
        # if x is nan dist is infinite
        n_cell[~np.isfinite(dist)] = -1

        return n_cell

    def are_points_inside_domain(self, xq):
        n_cell  = self.initial_cell_guess(xq)
        bc = self.get_bc_cords(xq,n_cell)
        is_inside=  np.all(np.logical_and(bc >= -self.params['bc_walk_tol'], bc  <= 1.+self.params['bc_walk_tol']),axis=1)
        return is_inside, n_cell  # is inside if  magnitude of all BC < 1

    #@function_profiler(__name__)
    def eval_field_interpolation_at_given_locations(self, field_instance,x, time=None,  output=None, n_cell= None):
        # in  evaluation of field interpolation at specific locations, ie not particle locations
        #todo only time_dependent_2Dfield  working - eval_field_interpolation_at_given_locations
        # todo add time dependence/ time fractions
        # does this over write paricle props??
        si = self.shared_info
        reader = si.classes['reader']

        part_prop = si.classes['particle_properties']
        part_prop_struct = si.classes['particle_group_manager'].part_prop_as_struct
        grid_struct = self.grid_as_struct
        st = self.step_info

        # is no output name give particle property for output is same as hindcast fieldName
        if output is None:
            if  field_instance.data.shape[3]> 1:
                output= np.full((x.shape[0], field_instance.data.shape[3]), np.nan)
            else:
                output = np.full((x.shape[0],),np.nan)

        if n_cell is None:
            n_cell= self.initial_cell_guess(x)

        # get bc cords for the cells
        bc_cords = self.get_bc_cords(x, n_cell)
        active = np.arange(x.shape[0])
        # args the same for all
        args = (basic_util.atLeast_Nby1(output),
                field_instance.data, grid_struct,
                part_prop_struct,
                active, st)

        if field_instance.is_time_varying():
            # get buffer time step and time fraction
            nt = reader.time_to_hydro_model_index(time)
            nb = reader.buffer_index_to_buffer_offset(nt)

            if field_instance.is3D():
                if field_instance.params['name']=='water_velocity':
                    # 3D vel needs log layer interp in bottom cell
                    eval_interp.eval_water_velocity_3D(*args)
                else:
                    eval_interp.time_dependent_3Dfield(*args)
            else:
                # todo 2D time dep not not working yet
                eval_interp.time_dependent_2Dfield(*args)
        else:
            # 2D or 3D non-time varying
            if field_instance.is3D():
                # todo eval_interp3D_timeIndependent not implemented for 3D non-time varying fields
                nz_nodes = part_prop['nz_cell'].data
                z_fraction_nodes = part_prop['z_fraction_nodes'].data
                raise Exception('eval_field_interpolation_at_given_locations: spatial interp using eval_interp3D_timeIndependent not implemented yet ')
            else:
                # is working
                eval_interp.time_independent_2Dfield(*args)
                return  output

    def get_bc_cords(self,x,n_cells):
        # get BC cords for given x's
        si= self.shared_info
        grid = si.classes['reader'].grid
        bc_cords = np.full((x.shape[0],3), 0.)
        tri_interp_util.get_BC_cords_numba(x, n_cells, grid['bc_transform'], bc_cords)
        return bc_cords

    def update_dry_cells(self):
        # update 0-255 dry cell index
        eval_interp.update_dry_cell_index(self.grid_as_struct,self.step_info)

    def close(self):
        si=self.shared_info
        info = self.info
        # transfer walk / step info from to class attributes to write in case_info file

        w = info['walk_info']
        for name in self.step_info.dtype.names:
            w[name] = self.step_info[name]
     
        w['average_number_of_triangles_walked']= w['number_of_triangles_walked']/max(1,w['particles_located_by_walking'])
        if si.is_3D_run:
            w['average_vertical_walk_steps'] = w['total_vertical_steps_walked'] / max(1, w['particles_located_by_walking'])

        f = f" Triangle walk summary: Of  {w['particles_located_by_walking']:6,d} particles located "
        f += f" {w['triangle_walks_retried']:1d}, walks were too long and were retried, "
        f += f" of these  {w['particles_killed_after_triangle_walk_retry_failed']:1d} failed after retrying and were discarded"
        si.msg_logger.progress_marker(f)

        if w['triangle_walks_retried'] > 100:
            si.msg_logger.msg(f" Of {w['particles_located_by_walking']:3d} particles located {w['triangle_walks_retried']:3d}, were to long and restated from initial guess",
                              crumbs='Interpolator calls, InterpTriangularNativeGrid_Slayer_and_LSCgrid',
                              hint= f"This number of retries can be reduced by decreasing the time step.")

        if w['particles_killed_after_triangle_walk_retry_failed'] > 0:
            si.msg_logger.msg(f" Of {w['particles_located_by_walking']:3d} particles located {w['particles_killed_after_triangle_walk_retry_failed']:3d}, failed to find cell",
                              crumbs='Interpolator calls, InterpTriangularNativeGrid_Slayer_and_LSCgrid',
                              hint= f"Try increasing interpolator parameter 'max_search_steps', current value ={self.params['max_search_steps']:3d}")




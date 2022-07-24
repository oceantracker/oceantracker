# linear interploation for triangles in both space and time


#todo  are BC cords as np.float32, faster as lower memory transfer demand and good enough?
import numpy as np

from scipy.spatial import cKDTree

from oceantracker.interpolator._base_interp import _BaseInterp
from oceantracker.util import basic_util
from oceantracker.interpolator.util import triangle_interpolator_util
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

        # build kd tree for initial triangle find of particle initial locations
        xy_centriod = np.mean(si.grid['x'][si.grid['triangles']], axis=1)
        self.KDtree = cKDTree(xy_centriod)

        self.code_timer.stop('intialize_interplolation_grid')
        # create particle properties to  store history of current triangle  for reuse

        p = si.classes['particle_group_manager']
        p.create_particle_property('manual_update',dict(name='n_cell',  write=False, dtype=np.int32,
                                   initial_value=0))  # start with cell number guess of zero
        p.create_particle_property('manual_update',dict(name='bc_cords',  write=False, initial_value=0., vector_dim=3))

        # BC walk stats
        info = self.info
        info['n_total_walking_steps'] = 0
        info['n_total_vertical_search_steps'] = 0
        info['n_total_particles_located'] =0
        info['n_max_walking_steps'] =0
        info['failed_searches'] = 0
        info['count_maybe_below_bottom'] = 0
        info['count_maybe_above_surface'] = 0

        if si.hindcast_is3D:
            # space to record vertical cell for each particles triangle at two timer steps  for each node in cell containing particle
            # used to do 3D time dependent interploation
            p.create_particle_property('manual_update',dict(name='nz_cell_nodes',  write=False, dtype=np.int8,
                                       initial_value=0, vector_dim=2, prop_dim3=3))
            p.create_particle_property('manual_update',dict(name='z_fraction_nodes',  write=False, dtype=np.single,
                                       initial_value=0., vector_dim=2, prop_dim3=3))

    def build_grid(self):
        si = self.shared_info

        # build transformation matrix to calculate bc cords in same form as scipy qhulll
        si.grid['bc_transform'] = triangle_interpolator_util.get_BC_transform_matrix(si.grid['x'].data, si.grid['triangles'].data)


    def find_cell(self, xq, nb,step_dt_fraction, active):
        # locate cell in place
        # nt give but not needed in 2D
        si= self.shared_info
        self.code_timer.start('find_cells_and_weights')

        self.locate_BCwalk(xq, nb,step_dt_fraction, active)  # best method!
        self.code_timer.stop('find_cells_and_weights')

        self.info['n_total_particles_located'] += active.shape[0]

        if si.hindcast_is3D:
            self.code_timer.start('find_depth_cell')
            self.get_depth_cell(xq, nb, step_dt_fraction, active)

            #print('vcell', self.info['n_total_vertical_search_steps'] / active.shape[0])
            self.code_timer.stop('find_depth_cell')

    def locate_BCwalk(self,xq, nb,step_dt_fraction, active):
        # Bary Centric walk, flags land triangles in numba code
        si = self.shared_info
        part_prop = si.classes['particle_properties']

        nsteps, nmax = triangle_interpolator_util.BCwalk_with_move_backs_numba(
                                                    xq,
                                                    part_prop['x_last_good'].data,
                                                    nb, step_dt_fraction,
                                                    part_prop['status'].data,
                                                    part_prop['n_cell'].data,
                                                    part_prop['bc_cords'].data,
                                                    si.grid['bc_transform'],
                                                    si.grid['adjacency'],
                                                    si.grid['is_dry_cell'],
                                                    self.params['bc_walk_tol'],
                                                    self.params['max_search_steps'],
                                                    si.case_params['run_params']['open_boundary_type'] == 1,
                                                    active)
        sel = part_prop['status'].find_subset_where(active, 'eq', si.particle_status_flags['cell_search_failed'], out =self.get_particle_subset_buffer())
        if sel.shape[0] > 0 :
            self.code_timer.start('kd-tree_retrys')
            new_cell = self.initial_cell_guess(xq[sel,:2])
            part_prop['n_cell'].set_values(new_cell, sel)

            nsteps, nmax = triangle_interpolator_util.BCwalk_with_move_backs_numba(
                                            xq,
                                            part_prop['x_last_good'].data,
                                            part_prop['status'].data,
                                            part_prop['n_cell'].data,
                                            part_prop['bc_cords'].data,
                                            si.grid['bc_transform'], si.grid['adjacency'],
                                            self.params['bc_walk_tol'],
                                            self.params['max_search_steps'],
                                            si.case_params['run_params']['open_boundary_type'] == 1,
                                            sel)

            sel = part_prop['status'].find_subset_where(sel, 'eq', si.particle_status_flags['cell_search_failed'], out=self.get_particle_subset_buffer())
            if sel.shape[0] > 0:
                si.case_log.write_warning('Some BC walks too long after kd retry- killed ' + str(sel.shape[0]) + ' particles')
                self.info['failed_searches'] += sel.shape[0]
                # make notes for log file enabling follow up
                si.case_log.write_warning('failed BCwalks_after_KDtree_retry, particles' + str(sel.tolist()) + ' xq =' + str(xq[sel, :].tolist()))
                # kill particles
                part_prop['status'].set_values(si.particle_status_flags['dead'], sel)
            self.code_timer.stop('kd-tree_retrys')

        # note largest number of triangles walked
        if nmax > self.info['n_max_walking_steps']:
            self.info['n_max_walking_steps'] = nmax
        self.info['n_total_walking_steps'] += nsteps

    def initial_cell_guess(self, xq):
        # find nearest cell   #todo not sure error checking is used
        si=self.shared_info
        dist, n_cell = self.KDtree.query(xq[:, :2])
        n_cell[np.any(~np.isfinite(xq), axis=1)] = -1 # stops walking for non-finite initial cords
        return n_cell

    def are_points_inside_domain(self, xq):
        si=self.shared_info

        # first use KD tree to find nearest cell
        dist, n_cell = self.KDtree.query(xq[:, :2])
        bc= np.full((xq.shape[0],3), -1.0)

        # find Barycenteric cords of point in the nearest cell
        triangle_interpolator_util.get_BC_cords_numba(xq, n_cell, si.grid['bc_transform'], bc)
        return np.all( np.logical_and(bc >= 0.,  bc <= 1.),axis=1), n_cell  # is inside if  magitude of all BC < 1

    def eval_field_interpolation_at_particle_locations(self, fieldObj, nb  , output, active, step_dt_fraction=None):
        # in place evaluation of field interpolation
        si = self.shared_info
        part_prop= si.classes['particle_properties']
        n_cell   = part_prop['n_cell'].data
        bc_cords = part_prop['bc_cords'].data

        if fieldObj.is_time_varying():
            if fieldObj.is3D():
                nz_nodes = part_prop['nz_cell_nodes'].data
                z_fraction_nodes = part_prop['z_fraction_nodes'].data
                triangle_interpolator_util.interp_3Dfield_inPlace_time_depenent(basic_util.atLeast_Nby1(output),
                                                                                 fieldObj.get_data(nb=nb),
                                                                                 fieldObj.get_data(nb=nb + 1),
                                                                                 step_dt_fraction,
                                                                                 si.grid['triangles'],
                                                                                 n_cell,
                                                                                 nz_nodes, z_fraction_nodes, bc_cords, active)
            else:
                triangle_interpolator_util.interp_2Dfield_inPlace_timeDependent(basic_util.atLeast_Nby1(output),
                                                                                 fieldObj.get_data(nb=nb),
                                                                                 fieldObj.get_data(nb=nb + 1),
                                                                                 step_dt_fraction,
                                                                                 si.grid['triangles'],
                                                                                 n_cell,
                                                                                 bc_cords, active)
        else:
            # 2D or 3D non-time varying
            if fieldObj.is3D():
                # todo eval_interp3D_timeIndependent not implented for 3D non-time varying fields
                nz_nodes = part_prop['nz_cell_nodes'].data
                z_fraction_nodes = part_prop['z_fraction_nodes'].data
                raise Exception('eval_field_interpolation_at_particle_locations : spatial interp using eval_interp3D_timeIndependent not implemented yet ')
            else:
                triangle_interpolator_util.eval_interp_spatial_timeIndependent_2Dfield_inPlace_numba(basic_util.atLeast_Nby1(output),
                                                                                                      fieldObj.get_data(nb=0),
                                                                                                      si.grid['triangles'],
                                                                                                      n_cell,
                                                                                                      bc_cords, active)

    def eval_field_interpolation_at_given_locations(self, fieldObj,x, time=None,  output=None, n_cell= None):
        # in  evaluation of field interpolation at specific locations, ie not particle locations
        si = self.shared_info
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
        bc_cords = np.full((x.shape[0],3), 0.)
        triangle_interpolator_util.get_BC_cords_numba(x, n_cell, si.grid['bc_transform'], bc_cords)
        active = np.arange(x.shape[0])

        if fieldObj.is_time_varying():
            # get buffer time step and time fraction
            nt = reader.time_to_global_time_step(time)
            nb = reader.global_index_to_buffer_index(nt)
            step_dt_fraction = abs(time - reader.get_particle_time(nb)) / si.hindcast_time_step

            if fieldObj.is3D():
                #todo not working, find depth cells
                z_fraction_nodes = part_prop['z_fraction_nodes'].data
                nz_nodes = part_prop['nz_cell_nodes'].data
                triangle_interpolator_util.interp_3Dfield_inPlace_time_depenent(basic_util.atLeast_Nby1(output),
                                                                                 fieldObj.get_data(nt_buffer=nb),
                                                                                 fieldObj.get_data(nt_buffer=nb + 1),
                                                                                 step_dt_fraction,
                                                                                 si.grid['triangles'],
                                                                                 n_cell,
                                                                                 nz_nodes, z_fraction_nodes, bc_cords, active)
            else:
                # todo not working, find depth cells
                triangle_interpolator_util.interp_2Dfield_inPlace_timeDependent(basic_util.atLeast_Nby1(output),
                                                                                 fieldObj.get_data(nt_buffer=nb),
                                                                                 fieldObj.get_data(nt_buffer=nb + 1),
                                                                                 step_dt_fraction,
                                                                                 si.grid['triangles'],
                                                                                 n_cell,
                                                                                 bc_cords, active)
        else:
            # 2D or 3D non-time varying
            if fieldObj.is3D():
                # todo eval_interp3D_timeIndependent not implemented for 3D non-time varying fields
                nz_nodes = part_prop['nz_cell_nodes'].data
                z_fraction_nodes = part_prop['z_fraction_nodes'].data
                raise Exception('eval_field_interpolation_at_given_locations: spatial interp using eval_interp3D_timeIndependent not implemented yet ')
            else:
                # is working
                triangle_interpolator_util.eval_interp_spatial_timeIndependent_2Dfield_inPlace_numba(basic_util.atLeast_Nby1(output),
                                                                                                      fieldObj.get_data(nb=0),
                                                                                                      si.grid['triangles'],
                                                                                                      n_cell,
                                                                                                      bc_cords, active)
                return  output

    def get_depth_cell(self, xq, nb, step_dt_fraction,active):
        # find depth cell number starting with a guess of previous depth cell
        # for fixed fractional depth grid
        si = self.shared_info
        part_prop = si.classes['particle_properties']

        zlevel_nodes= si.grid['zlevel']
        nz_bottom = si.grid['bottom_cell_index']
        n_cell      = part_prop['n_cell'].data
        nz_nodes    = part_prop['nz_cell_nodes'].data
        status      = part_prop['status'].data
        BCcords     = part_prop['bc_cords'].data
        z_fraction_nodes = part_prop['z_fraction_nodes'].data
        #z=part_prop['x'].data[:10,2]
        n_vertical_searches, count_maybe_below_bottom, count_maybe_above_surface = \
                                triangle_interpolator_util.get_depth_cell_time_varying_Slayer_or_LSCgrid(
                                                        xq[:, 2], nb, step_dt_fraction, zlevel_nodes, si.grid['triangles'], n_cell,
                                                        nz_bottom, BCcords, status,
                                                        si.particle_status_flags['on_bottom'], si.particle_status_flags['moving'],
                                                        si.particle_status_flags['stranded_by_tide'],
                nz_nodes, z_fraction_nodes, active)
        info = self.info
        info['n_total_vertical_search_steps'] += n_vertical_searches
        info['count_maybe_below_bottom'] += count_maybe_below_bottom
        info['count_maybe_above_surface'] += count_maybe_above_surface

    def close(self):
        info = self.info
        info['mean_number_of_triangles_walked'] = info['n_total_walking_steps'] / info['n_total_particles_located']
        # there are vertical searches at 3 nodes and 2 time steps
        info['mean_number_of_vertical_search_steps_per_cell_search'] = info['n_total_vertical_search_steps'] / info['n_total_particles_located']

        info['mean_count_maybe_below_bottom_per_cell_search' ] = info['count_maybe_below_bottom'] / info['n_total_particles_located']
        info['mean_count_maybe_above_surface_per_cell_search'] = info['count_maybe_above_surface'] / info['n_total_particles_located']

# Below is numpy version of numba BC cord code, now only used as check
#________________________________________________
    def get_cell_cords_check(self,x,n_cell):
        # barycentric cords, only for use with non-improved scipy and KDtree for al time steps
        # numba code does this faster
        si = self.shared_info
        TT = np.take(si.grid['bc_transform'], n_cell, axis=0,)
        b = np.full((x.shape[0],3), np.nan, order='C')
        b[:,:2] = np.einsum('ijk,ik->ij', TT[:, :2], x[:, :2] - TT[:, 2], order='C')  # Einstein summation
        b[:,2] = 1. - b[:,:2].sum(axis=1)
        return b




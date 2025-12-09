# linear interploation for triangles in both space and time
#todo  are BC cords as np.float32, faster as lower memory transfer demand and good enough?
import numpy as np
from oceantracker.interpolator._base_interp import _BaseInterp
from time import perf_counter
from oceantracker.interpolator.util import triangle_interpolator_util as tri_interp_util ,  triangle_eval_interp
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC
from oceantracker.shared_info import shared_info as si
from oceantracker.interpolator._find_hori_cell_triangle_walk import FindHoriCellTriangleWalk
from oceantracker.interpolator._eval_interp_triangles import EvalInterpTriangles
from oceantracker.interpolator import _find_vertical_cell_classes
from oceantracker.particle_properties.util import particle_comparisons_util

class  InterpTriangularGrid(_BaseInterp):

    # uses tweaked sci py which allows using start triangle location
    def add_required_classes_and_settings(self):
        info = self.info


    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({'bc_walk_tol': PVC(1.0e-3, float,min = 0.),
                                 'max_search_steps': PVC(500,int, min =1)})
        self.info['current_buffer_index'] = np.zeros((2,), dtype=np.int32)
        self.info['bad_z_fraction_count'] = 0
    def add_required_classes_and_settings(self):
        info = self.info


    def initial_setup(self, reader):
        super().initial_setup(reader)  # children must call this parent class to default shared_params etc
        params = self.params
        grid = reader.grid

        t0 = perf_counter()
        crumbs = 'Interpolator initial_setup '

        # define initial cell and find cell functions from interp class
        self._hori_cell_finder= FindHoriCellTriangleWalk(grid, params)
        self.find_initial_hori_cell_method= self._hori_cell_finder.find_initial_hori_cell
        self.info['horizontal_cell_finder_info'] = self._hori_cell_finder.info
        self._get_hori_cell = self._hori_cell_finder.find_cell

        self._interp_evaluator = EvalInterpTriangles(params, reader)

        if reader.info['is3D']:
            # space to record vertical cell for each particles' triangle at two timer steps  for each node in cell containing particle
            # used to do 3D time dependent interpolation
            si.add_class('particle_properties', name ='nz_cell', class_name='ManuallyUpdatedParticleProperty',write=False, dtype='int32',
                         initial_value=0, caller=self,crumbs=crumbs) # todo  create  initial serach for vertical cell
            si.add_class('particle_properties', name ='z_fraction',class_name='ManuallyUpdatedParticleProperty',write=False, dtype='float32',
                         initial_value=0., caller=self,crumbs=crumbs)
            si.add_class('particle_properties', name ='z_fraction_water_velocity',class_name='ManuallyUpdatedParticleProperty',write=False, dtype='float32',
                         initial_value=0., description=' thickness of bottom layer in meters, used for log layer velocity interp in bottom layer', caller=self,crumbs=crumbs)

            # set up vertical grid
            vgt= si.vertical_grid_types
            match  reader.info['vert_grid_type']:
                case vgt.Sigma:
                    self._vert_cell_finder= _find_vertical_cell_classes.FindVerticalCellSigmaGrid(grid, params) # make sigma map

                case vgt.Slayer | vgt.LSC:
                    self._vert_cell_finder = _find_vertical_cell_classes.FindVerticalCellSlayerLSCGrid(grid, params)
                case vgt.Zfixed:
                    self._vert_cell_finder = _find_vertical_cell_classes.FindVerticalCellZfixed(grid, params)


    def final_setup(self):

        # set up a grid class,part_prop and vertical cell find functions to minimise numba function arguments

        info = self.info

        # create particle properties to  store history of current triangle  for reuse

        # set up place for walk info failures
        info['tri_walk_full_failures'] = []

        # set up walk count vector and map to info
        self.walk_counts=np.zeros((8,),dtype=np.int64)
        wc = self.walk_counts
        info.update(dict(   particles_located_by_walking = wc[0:1],
                            number_of_triangles_walked = wc[1:2],
                            longest_triangle_walk = wc[2:3],
                            nans_encountered_triangle_walk = wc[3:4],
                            triangle_walks_retried = wc[4:5],
                            particles_killed_after_triangle_walk_retry_failed = wc[5:6],
                            total_vertical_steps_walked = wc[6:7],
                            longest_vertical_walk = wc[7:8])
                            )

    def interp_field(self,field_instance,current_buffer_steps, fractional_time_steps,
                                output, active):
        ie= self._interp_evaluator
        fi = field_instance

        match (fi.is3D(), fi.is_time_varying(), fi.is_vector() ):
            case (False, False, False):
                ie._time_independent_2D_scalar_field(fi,current_buffer_steps,
                                       fractional_time_steps,output, active)

            case (False, False, True):
                ie._time_independent_2D_vector_field(fi,current_buffer_steps,
                                       fractional_time_steps,output, active)

            case (False, True, False):
                ie._time_dependent_2D_scalar_field(fi,current_buffer_steps,
                                       fractional_time_steps,output, active)
            case (False, True, True):
                ie._time_dependent_2D_vector_field(fi, current_buffer_steps,
                                                   fractional_time_steps, output, active)

            case (True, True, False): # eg 3D scalars, eg temperature
                ie._time_dependent_3D_scalar_field(fi, current_buffer_steps,
                                                   fractional_time_steps, output, active)

            case (True, True, True):# eg 3D vector, eg water velocity
                ie._time_dependent_3D_vector_field(fi, current_buffer_steps,
                                                   fractional_time_steps, output, active)
            case _:
                si.msg_logger.msg (f' 3D time invariant fields interpolator not yet implemented for ', error=True, caller=self,
                                   hint=f'remove field "{str(fi.params["name"])}" from reader load_fields param')
        pass

    def find_hori_cell(self,xq, active):
        # do cell walk
        t0= perf_counter()
        info = self.info
        part_prop = si.class_roles.particle_properties

        self._get_hori_cell(xq, active)

        # try to fix any failed walks
        IDs_need_fixing =part_prop['cell_search_status'].compare_all_to_a_value('lt', si.cell_search_status_flags.ok,
                                                                           out=self.get_partID_buffer('B1'))
        # retry any failed walks, ie too long
        sel_failed_walk = part_prop['cell_search_status'].data[IDs_need_fixing] == si.cell_search_status_flags.failed

        if np.any(sel_failed_walk):
            IDs_failed_walk = IDs_need_fixing[sel_failed_walk]
            info['triangle_walks_retried'] += IDs_failed_walk.size

            n_cell, bc, is_inside_domain = self.find_initial_hori_cell_method(xq[IDs_failed_walk,...])
            fixed = is_inside_domain
            part_prop['n_cell'].set_values(n_cell[fixed], IDs_failed_walk[fixed])
            part_prop['bc_coords'].set_values(bc[fixed,:], IDs_failed_walk[fixed])

            # recheck for repeated failures of failed searched, which must be outside domain if not found by intial serarch
            if np.any(~fixed):
                sel2= IDs_failed_walk[~fixed]
                wf = {'x0': part_prop['x_last_good'].get_values(sel2),
                      'xq': part_prop['x'].get_values(sel2)}

                info['tri_walk_full_failures'].append(wf)
                info['particles_killed_after_triangle_walk_retry_failed'] += sel2.size  # total failed walks
                si.msg_logger.msg('walks too long after kd retry- killed ' + str(sel2.size) + ' particles', warning=True, tabs=0,
                                  hint='Try decreasing time step or increasing interpolator parameter "max_search_steps", current value =' + str(self.params['max_search_steps']))
                # make notes for log file enabling follow up
                si.msg_logger.msg('particle locations of failed walks, first 3 or less ', warning=True, tabs=2)
                si.msg_logger.msg(' location xq =' + str(xq[sel2[:3], :].tolist()), warning=True, tabs=2)
                si.msg_logger.msg(' x_old =' + str(part_prop['x_last_good'].data[sel2[:3], :].tolist()), warning=True, tabs=2)
                # kill particles
                part_prop['status'].set_values(si.particle_status_flags.dead, sel2)

        si.block_timer('Find horizontal cell', t0)

        return IDs_need_fixing

    def find_vertical_cell(self, fields, xq, current_buffer_steps,fractional_time_steps, active):
        # locate vertical cell in place
        info = self.info
        t0 = perf_counter()
        info['bad_z_fraction_count'] = self._vert_cell_finder.find_vertical_cell(fields, xq, current_buffer_steps, fractional_time_steps, active)
        if info['bad_z_fraction_count'] > 0 :
            si.msg_logger.msg(f'Out of range vertical layer fraction calculated, number counted so far {info["bad_z_fraction_count"]}', strong_warning=True,caller = self,
            hint='issue with 3D vertical grid hindcast values? reader encountered unknown variant of hindcast vertical grid?')

        si.block_timer('Find vertical cell', t0)

    def are_points_inside_domain(self,xq):
        n_cell, bc, is_inside_domain  = self.find_initial_hori_cell_method(xq)
        part_data = dict(x = xq, n_cell=n_cell, bc_coords=bc)
        # todo add interpolated water depth, tide???
        return is_inside_domain, part_data # is inside if  magnitude of all BC < 1

    def get_bc_coords(self,grid, x,n_cells):
        # get BC cords for given x's
        bc_coords = np.full((x.shape[0],3), 0.)
        tri_interp_util.calc_BC_cords_numba(x, n_cells, grid['bc_transform'], bc_coords)
        return bc_coords

    def close(self):
        info = self.info
        # transfer walk / step info from to class attributes to write in case_info file

        self._hori_cell_finder.close()




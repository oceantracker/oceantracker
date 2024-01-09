from oceantracker.field_group_manager.field_group_manager import FieldGroupManager
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util.parameter_util import make_class_instance_from_params
from oceantracker.util.time_util import seconds_to_isostr
from time import  perf_counter
from copy import copy
# run fields nested with outer main readers grid

class DevNestedFields(ParameterBaseClass):
    readers=[] # first is outer grid, nesting the others

    def initial_setup(self):
        si = self.shared_info
        ml = si.msg_logger
        # setup outer grid first

        self.fgm_outer_grid = make_class_instance_from_params('field_group_manager_outer_grid',
                                dict(class_name='oceantracker.field_group_manager.field_group_manager.FieldGroupManager'),
                                ml,   crumbs='adding outer hydro-grid field manager for nested grid run' )
        self.fgm_outer_grid.initial_setup()

        # note es to check if all hidcasts have same required info

        has_A_Z_profile = self.fgm_outer_grid.info['has_A_Z_profile']
        self.hydro_time_step = self.fgm_outer_grid.get_hydo_model_time_step()
        self.start_time, self.end_time  = self.fgm_outer_grid.get_hindcast_start_end_times()

        self.fgm_nested_grids = []
        for name, params in si.working_params['nested_reader_builders'].items():
            ml.progress_marker(f'Starting nested grid setup #{len(self.fgm_nested_grids)}, name= "{name}"')

            t0= perf_counter()
            i =  make_class_instance_from_params(name,
                                dict(class_name='oceantracker.field_group_manager.field_group_manager.FieldGroupManager'),
                                ml,   crumbs=f'adding nested hydro-model field manager #{len(self.fgm_nested_grids)}' )


            i._setup_hydro_reader(params)
            i.set_up_interpolator()


            self.fgm_nested_grids.append(i)

            # record consitency info
            has_A_Z_profile = has_A_Z_profile and i.info['has_A_Z_profile']
            self.hydro_time_step = min(self.hydro_time_step,i.get_hydo_model_time_step())

            # start and end times
            times= i.get_hindcast_start_end_times()
            self.start_time, self.end_time=  max(self.start_time,times[0]), min(self.end_time,times[1])

            ml.progress_marker(f'Finished nested hydro-model grid setup #{len(self.fgm_nested_grids)}, name= "{name}", from {seconds_to_isostr(times[0])} to  {seconds_to_isostr(times[1])}', start_time=t0)

        #todo add check on overlaping

        # consistency checks
        # A_Z profile data
        if si.settings['use_A_Z_profile'] and not has_A_Z_profile:
            ml.msg(f'Not all hindcasts have A_Z profile variable, set "use_A_Z_profile" to False, to run with use constant dipersion A_Z',
                   crumbs='Nested reader set up ',fatal_error=True, exit_now=True)

        self.info['has_A_Z_profile'] = has_A_Z_profile # set

        # dry cell flag
        if si.settings['write_dry_cell_flag']:
            ml.msg(f'Cannot write dry cell flag to tracks files for nested grids, disabling dry cell writes',
                   crumbs='Nested reader set up ',  note=True)
            si.settings['write_dry_cell_flag'] = False

        #todo check hindcasts over lap

        pass

    def final_setup(self):
        # set up outer grid with interplotor required particle properties
        self.fgm_outer_grid.final_setup()


        pass

    def update_reader(self, time_sec):
        self.fgm_outer_grid.update_reader(time_sec)

    def get_hydo_model_time_step(self): return self.hydro_time_step # return the smallest time step

    def get_hindcast_start_end_times(self):
        return self.start_time, self.end_time

    def add_part_prop_from_fields_plus_book_keeping(self):
        si = self.shared_info
        # only use outer grid to add properties for all readers
        self.fgm_outer_grid.add_part_prop_from_fields_plus_book_keeping()

        # add grid index part prop to track which grid particle is currently in
        pgm = si.classes['particle_group_manager']
        pgm.add_particle_property('gridID',  'manual_update', dict(write=False, time_varying=True, dtype=np.int8, initial_value=-1))

    def are_points_inside_domain(self,x):
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        # set up space
        N= x.shape[0]
        is_inside= np.full((N,),False)
        n_cell    = np.full((N,), si.particle_status_flags['unknown'],dtype=np.float32)
        bc  = np.full((N,3), -1, dtype=np.float64)
        gridID = np.full((N,), -1, dtype=np.int8)

        # first see if inside any nested grid
        for n, i in enumerate(self.fgm_nested_grids):
            is_inside_n, n_cell_n, bc_n = i.are_points_inside_domain(x)

            #record those inside this grid
            is_inside[is_inside_n] = True
            n_cell[is_inside_n] = n_cell_n[is_inside_n]
            bc[is_inside_n] = bc_n[is_inside_n]
            gridID[is_inside_n] = n+1
            pass

        # first see if inside out at outer grid
        is_inside, n_cell, bc = self.fgm_outer_grid.are_points_inside_domain(x)
        pass




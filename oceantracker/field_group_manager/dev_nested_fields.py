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
        self.fgm_outer_grid._setup_hydro_reader(si.working_params[ 'reader_builder'])

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



            self.fgm_nested_grids.append(i)

            # record consitency info
            has_A_Z_profile = has_A_Z_profile and i.info['has_A_Z_profile']
            self.hydro_time_step = min(self.hydro_time_step,i.get_hydo_model_time_step())

            # start and end times
            times= i.get_hindcast_start_end_times()
            self.start_time, self.end_time=  max(self.start_time,times[0]), max(self.start_time,times[0])

            ml.progress_marker(f'Finished nested hydro-model grid setup #{len(self.fgm_nested_grids)}, name= "{name}", from {seconds_to_isostr(times[0])} to  {seconds_to_isostr(times[1])}', start_time=t0)


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

    def get_hydo_model_time_step(self): return self.hydro_time_step # return the smallest time step

    def get_hindcast_start_end_times(self):
        return self.start_time, self.end_time
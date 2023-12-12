from oceantracker.field_group_manager.field_group_manager import FieldGroupManager
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util.parameter_util import make_class_instance_from_params
from time import  perf_counter
# run fields nested with outer main readers grid

class DevNestedFields(ParameterBaseClass):
    readers=[] # first is outer grid, nesting the others

    def initial_setup(self):
        si = self.shared_info
        ml = si.msg_logger
        # setup outer grid first

        self.fgm_outer_grid = make_class_instance_from_params('field_group_manager_outer_grid',
                                dict(class_name='oceantracker.field_group_manager.field_group_manager.FieldGroupManager'),
                                ml,   crumbs='adding outer grid field manager for nested grid run' )
        self.fgm_outer_grid._setup_hydro_reader(si.working_params['core_roles']['reader'])
        self.fgm_nested_grids=[]
        ml.progress_marker('Starting nested grid setup')
        for name, params in si.working_params['role_dicts']['nested_readers'].items():
            t0= perf_counter()
            i =  make_class_instance_from_params(name,
                                dict(class_name='oceantracker.field_group_manager.field_group_manager.FieldGroupManager'),
                                ml,   crumbs=f'adding nested grid field manager #{len(self.fgm_nested_grids)}' )
            i._setup_hydro_reader(params)
            ml.progress_marker(f'Finished nested grid setup #{len(self.fgm_nested_grids)}, name= "{name}"', start_time=t0)
            self.fgm_nested_grids.append(i)

        pass
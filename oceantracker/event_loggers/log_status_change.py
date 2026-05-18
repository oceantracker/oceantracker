from oceantracker.shared_info import  shared_info as si
from oceantracker.event_loggers.manual_event_logger import  ManualEventLogger
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC

class LogStatusChange(ManualEventLogger):
    '''
    log positions etc when staus changes to a new value
    not working yet!!
    '''
    development = True
    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params(particle_prop_to_write_list=
                  PLC([ 'ID','x','IDpulse', 'IDrelease_group', 'user_release_groupID',
                        'age','status', 'old_status'],str))

    def add_required_classes_and_settings(self):
        super().add_required_classes_and_settings()
        # add bookkeeping prop, but don't write to tracks file
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty',
                     name='new_status', initial_value=False, dtype='int8', write=False)
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty',
                     name='old_status', initial_value=False, dtype='int8', write=False)

    def initial_setup(self):
        params=self.params
        params['particle_prop_to_write_list'].append([])


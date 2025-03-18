from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty

# import the class that check user given parameters
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC, ParameterListChecker as PLC, ParameterCoordsChecker as PCC

from oceantracker.shared_info import shared_info as si # proces acees to all varaibles , classes and info
from oceantracker.util.numba_util import njitOT, njitOTparallel # numba decorators to make code fast 

class TimeAtStatus(CustomParticleProperty):
    ''' class to calculate the time each particle spends in a given status '''

    def __init__(self):
        super().__init__() # must call parent class to get its parameters etc 

        self.add_default_params( status= PVC(si.particle_status_flags.moving), possible_values =si.particle_status.possible_values(),
                                                docstr='The particle status to count the time spend' ) 
        
    def initial_setup(self):
        # any set up operations, or extra checks on paramters
        if self.params['status'] < si.particle_status_flags.moving:
            si.msg_logger.msg('Can only count times for particles which have statuses above stationary',caller = self, 
                              hint= f' status must, be stationary, on_bottom, stranded or moving ', fatal_error=True)
            
        

    def final_setup(self):
        # anything that must be done after all classes have done intial setup
        pass
    
    def update(self, n_time_step, time_sec, active):
        # find  the 
        part_prop = si.class_roles.particle_properties # a dict of all  particle properties

        return super().update(n_time_step, time_sec, active)
    
    @staticmethod
    def _add_time(count_status, status, total_time, active):
        
        for n in active: # loop over inicies of active particles, ie above stationaroor 
            if old_status[n] == count_status and old_status[n] == count_statu
            pass
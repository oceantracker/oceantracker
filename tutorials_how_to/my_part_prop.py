from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty

# import the class that check user given parameters
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC, ParameterListChecker as PLC, ParameterCoordsChecker as PCC
from oceantracker.util.numpy_util import possible_dtypes
from oceantracker.shared_info import shared_info as si # proces access to all variables , classes and info
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange # numba decorators to make code fast
import numpy as np

class TimeAtStatus(CustomParticleProperty):
    ''' class to calculate the time each particle spends in a given status '''

    def __init__(self):
        super().__init__() # must call parent class to get its parameters etc 
        psf = si.particle_status_flags
        self.add_default_params( required_status= PVC(psf.moving, str, possible_values =[psf.stationary, psf.stranded_by_tide, psf.on_bottom, psf.moving],
                                                    doc_str='The particle status to count the time spend'),
                                description=PVC('total time particle spends in a given status', # optional description and units are added to part. prop. netcdf variables attributes
                                                   str, units='seconds'),
                                 dtype =PVC('float64', str,possible_values=possible_dtypes,)
                                  )

    def add_required_classes_and_settings(self,**kwargs):
        # any other classes required by this new class must be added within the method

        # add particle propterty to record what time the given status starts, for use to find duration of the time particle has the given status
        si.add_class('particle_properties', name='time_status_started', class_name='ManuallyUpdatedParticleProperty', write=False,# dont write property to tracks files
                     initial_value=np.nan,
                     dtype='float64',         caller=self # caller useful to show where errors originated
                     )

    def initial_setup(self):
        # add any set up operations for variables etc, or extra checks on paramters etc
        pass

    def initial_value_at_birth(self, new_part_IDs):
        # set the value given to this particle property when new particles are released
        self.set_values(0., new_part_IDs)  # set total time to zero when born

    def final_setup(self):
        # anything that must be done after all classes have done their initial setup,
        # if things that depend on the setup of other classes
        pass
    
    def update(self, n_time_step, time_sec, active):
        # accumulate time for each particle in required status for particle indices given in array "active"
        part_prop = si.class_roles.particle_properties # a dict of all  particle properties

        # do manual update of this particle properties data
        self._add_time(time_sec, self.params['required_status'],
                       part_prop['status_last_good'].data,  # for numba must pass reference to .data the properties numpy array
                       part_prop['status'].data,
                       part_prop['time_status_started'],
                       self.data,  # the data of this particle property holds the accumulating time in the required status
                       active)

        pass
    
    @staticmethod  # Numba code cannot use classes such as self, as Numba only understands basic python variable types and numpy arrays
    @njitOTparallel  # decorator speed up code using numba with parallel threads option
    def _add_time(time_sec, required_status, old_status, status,time_status_started, total_time, active):

        for nn in prange(active.size): # threaded parallel for loop over indices of active particles
            n = active[nn]
            if old_status[n] != required_status and status[n] == required_status:
                # particle has changed to the required status
                time_status_started[n] = time_sec # record the time that staus starts

            elif old_status[n] == required_status and status[n] != required_status and np.isfinite( time_status_started[n]):
                # status has changed from the required status and the clock has been started, ie time_status_started is not nan
                total_time[n] = time_sec - time_status_started[n]
            pass
from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty

# import the class that check user given parameters
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC, ParameterListChecker as PLC, ParameterCoordsChecker as PCC
from oceantracker.util.numpy_util import possible_dtypes
from oceantracker.shared_info import shared_info as si # proces access to all variables , classes and info
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange # numba decorators to make code fast

class TimeAtStatus(CustomParticleProperty):
    ''' class to calculate the time each particle spends in a given status '''

    def __init__(self):
        super().__init__() # must call parent class to get its parameters etc 
        self.add_default_params( required_status= PVC('moving', str,
                                        possible_values =[key  for key, item in si.particle_status_flags.items() if item >=0 ],
                                                    doc_str='The particle status to count the time spend'),
                                description=PVC('total time particle spends in a given status', # optional description and units are added to part. prop. netcdf variables attributes
                                                   str, units='seconds'),
                                 dtype =PVC('float64', str,possible_values=possible_dtypes)
                                  )

    def initial_setup(self):

        super().initial_setup() # for particle prop. must call parent to set up data array self.data

        # get numerical value of status flag for use in numba code below
        self.info['status_value']  = si.particle_status_flags[self.params['required_status']] # info use to hold useful data
    def initial_value_at_birth(self, new_part_IDs):
        # set the value given to this particle property when new particles are released
        self.set_values(0., new_part_IDs)  # set total time to zero when born

    def update(self, n_time_step, time_sec, active):
        # accumulate time for each particle in required status for particle indices given in array "active"
        part_prop = si.class_roles.particle_properties # a dict of all  particle properties

        # do manual update of this particle properties data
        self._add_time(self.info['status_value'] ,si.settings.time_step,
                       part_prop['status'].data,
                       self.data,  # the data of this particle property holds the accumulating time in the required status
                       active)

        pass


    @staticmethod  # Numba code cannot use classes such as self, as Numba only understands basic python variable types and numpy arrays
    @njitOTparallel  # decorator speed up code using numba with parallel threads option
    def _add_time(required_status, time_step, status, total_time, active):

        for nn in prange(active.size): # threaded parallel for loop over indices of active particles
            n = active[nn]
            if status[n] == required_status:
                total_time[n] += time_step # update is every time
            pass
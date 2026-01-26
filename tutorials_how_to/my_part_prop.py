from oceantracker.particle_properties._base_particle_properties import (
    _BaseParticleProperty,
)

# to avoid accidental parameterization error we use these functions
# where we define "valid input" for each configuration variable
from oceantracker.util.parameter_checking import (
    ParamValueChecker as PVC,
    ParameterTimeChecker as PTC,
    ParameterListChecker as PLC,
    ParameterCoordsChecker as PCC,
)

from oceantracker.util.numpy_util import possible_dtypes
from oceantracker.shared_info import (
    shared_info as si,
)  # proces access to all variables , classes and info
from oceantracker.util.numba_util import (
    njitOT,
    njitOTparallel,
    prange,
)  # numba decorators to make code fast


class TimeAtStatus(_BaseParticleProperty):
    """class to calculate the time each particle spends in a given status"""

    # the init method is what is called during the creation of the class instance
    def __init__(self):
        # this calls the parent class method, to maintain its functionality without copying the code
        super().__init__()
        # we add one new default parameter that tells the class which particles to count
        self.add_default_params(
            required_status=PVC(
                "moving",  # default type
                str,  # required variable type for this input parameter
                possible_values=[
                    key for key, item in si.particle_status_flags.items() if item >= 0
                ],
                doc_str="The particle status to count the time spend",
            ),
            description=PVC(
                # optional description and units are added to part. prop. netcdf variables attributes
                "total time particle spends in a given status",  # description
                str,
                units="seconds",
            ),
            # this will define the data type of the new particle property
            dtype=PVC("float64", str, possible_values=possible_dtypes),
        )

    # during the model setup phase, we run this code
    def initial_setup(self):

        # first we execute the "parent" (_BaseParticleProperty) "initial_setup" method again
        super().initial_setup()

        # next we select, based on user input, the status set for which we will calculate this particle property
        # this is stored in self.info, where most of the run time properties are stored
        self.info["status_value"] = si.particle_status_flags[
            self.params["required_status"]
        ]

    # this will be used to initialize the particle property for each particle during its creation
    # in our case "0" for zero seconds within the selected status
    def initial_value_at_birth(self, new_part_IDs):
        self.set_values(0.0, new_part_IDs)

    # the update class is what is called during the "actual" model run.
    # I.e. after every time step.
    # Hence, this function will be called the most frequently.
    # To make it fast, we will create a numba function (_add_time)
    # Alternatively, you can use numpy function for the "heavy lifting".
    # Pure python operations tend to be much slower, and might otherwise
    # slow down your simulation (check the timing information in the caseInfo)
    def update(self, n_time_step, time_sec, active):
        # All we wan't to do here is to accumulate time for each particle in required status
        # which are currently "active" (e.g. exist, in contrast of those not yet released or removed)

        # this just contains a dict of all particle properties
        part_prop = si.class_roles.particle_properties

        # add the time (i.e. time step size) that the selected (required status)
        # particles have been in that state
        self._add_time(
            self.info["status_value"],
            si.settings.time_step,
            part_prop["status"].data,
            self.data,  # the data of this particle property holds the accumulating time in the required status
            active,
        )

        pass

    # Numba code cannot use classes such as self, as Numba only understands basic python variable types and numpy arrays
    # the "@njit" decorator - which we slightly tweaked in @njitOTparallel - speeds up the code using numba and uses parallel threads
    @staticmethod
    @njitOTparallel
    def _add_time(required_status, time_step, status, total_time, active):
        # threaded parallel (prange) for-loop over indices of active particles
        for nn in prange(active.size): 
            n = active[nn]
            if status[n] == required_status:
                total_time[n] += time_step  
            pass

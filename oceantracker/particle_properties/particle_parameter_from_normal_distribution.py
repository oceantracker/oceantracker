from oceantracker.particle_properties._base_properties import ParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC

class ParticleParameterFromNormalDistribution(ParticleProperty):
    # particle property drawn from normal distribution at birth
    # eg individual particle fall velocity drawn from distribution
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'mean': PVC(0., float, is_required=True),
                                 'variance' : PVC(0., float, min= 0.,is_required=True),
                                 'time_varying': PVC(False,bool)})

    def initial_setup(self):
        super().initial_setup()

    def initial_value_at_birth(self, new_part_IDs):
        s= (new_part_IDs.shape[0],)
        # todo gives zeros for some reason, check it is being called at birth
        # if augment shape if vector
        if self.data.ndim ==2:  s= s + (self.data.shape[1],)

        self.set_values(self.params['mean']+ self.params['variance']*np.random.normal(size=s), new_part_IDs)


    def update(self, active): pass # manual update by default

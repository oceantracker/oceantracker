from oceantracker.particle_properties._base_properties import ParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC

class ConstantParticleProperty(ParticleProperty):
    #
    def __init__(self):
        super().__init__()
        self.class_doc(description='Constant particle property which does not vary in time, which can be used to calculate spatial and temporal statistics from particle properties')

        self.add_default_params({   'value': PVC(1., float,doc_str='Value of the particle property for each particle which does not vary with time'),
                                    'variance': PVC(None, float, min=0., doc_str='Optional variance of the value given to each individual particle, which then does not vary in time, drawn from normal distribution, with mean "value"  and given variance')})
    def check_requirements(self):
        pass

    def initial_value_at_birth(self, new_part_IDs):

        if self.params['variance'] is None:
            # all particles have the same value
            self.set_values(self.params['value'], new_part_IDs) # sets this properties values
        else:
            #particles have individual values drawn from random normal, which dont vary in time
            self.set_values(np.random.normal(loc= self.params['value'], scale=self.params['variance'], size=new_part_IDs.size), new_part_IDs)
            pass

    def update(self,active):
        # property constant with time so no update needed
        pass
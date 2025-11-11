from oceantracker.particle_properties._base_particle_properties import CustomParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC

from oceantracker.shared_info import shared_info as si

class ParticleLoad(CustomParticleProperty):
    '''
    Particle property which carries a constant load or mass, which can be used to calculate spatial and temporal statistics of this load or mass.
    '''
    def __init__(self):
        super().__init__()
        #todo extend to allow for decaying load and replace decaying particle class, with this more general property


        self.add_default_params({'initial_value': PVC(1., float,doc_str='Value of the particle property when it is released') })

    def add_required_classes_and_settings(self):
        info = self.info
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name=self.params['name'] + '_initial_value',time_varying=False, write=False)


    def initial_setup(self):
        super().initial_setup()


    def initial_value_at_birth(self, new_part_IDs):

        params = self.params

        self.set_values(params['initial_value'], new_part_IDs)


    def update(self,n_time_step,time_sec,active):
        # property constant with time so no update needed
        pass
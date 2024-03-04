from oceantracker.particle_properties._base_particle_properties import ParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC

class ParticleLoad(ParticleProperty):
    #
    def __init__(self):
        super().__init__()
        #todo extend to allow for decaying load and replace decaying particle class, with this more general property

        self.class_doc('Particle property which carries a load or mass, which can be used to calculate spatial and temporal statistics of this load or mass')

        self.add_default_params({'initial_value': PVC(1., float,doc_str='Value of the particle property when it is released') })

    def check_requirements(self):
        pass

    def initial_setup(self):
        super().initial_setup()
        si = self.shared_info
        info= self.info
        particles = si.classes['particle_group_manager']

        particles.add_particle_property(self.info['name']+'_initial_value','manual_update',dict(time_varying=False, write=False))

    def initial_value_at_birth(self, new_part_IDs):

        params = self.params

        if len(params['release_group_parameters']) == 0:
            # all particles have same initial value
            self.set_values(params['initial_value'], new_part_IDs)


    def update(self,active):
        # property constant with time so no update needed
        pass
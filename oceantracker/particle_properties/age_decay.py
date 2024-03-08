from oceantracker.particle_properties._base_particle_properties import ParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
class AgeDecay(ParticleProperty):

    def __init__(self):
        super().__init__()
        self.add_default_params({ 'initial_value': PVC(1., float,doc_str='Particle property at the time of release'),
                                 'decay_time_scale': PVC( 1.*3600*24, float)})
        self.class_doc('Exponentially decaying particle property based on age.')

    def check_requirements(self):
      self.check_class_required_fields_prop_etc(required_props_list=['age'])



    def initial_value_at_birth(self, new_part_IDs):
        self.set_values(self.params['initial_value'], new_part_IDs) # sets this properties values

    def update(self,n_time_step, time_sec,active):
        # update decay prop each time step
        age = self.shared_info.classes['particle_properties']['age'].get_values(active)
        val = self.params['initial_value']*np.exp(-np.abs(age) / self.params['decay_time_scale'])
        self.set_values(val,active)
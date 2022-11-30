from oceantracker.particle_properties._base_properties import ParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
class AgeDecay(ParticleProperty):

    def __init__(self):
        super().__init__()
        self.add_default_params({'name': PVC('age_decay', str) ,
                                 'initial_value': PVC(1., float,doc_str='Particle property at the time of release'),
                                 'decay_time_scale': PVC( 1.*3600*24, float)})
        self.class_doc(description='Exponentially decaying particle property based on age.')

    def check_requirements(self):
        msg_list = self.check_class_required_fields_prop_etc(required_props_list=['age'])
        return msg_list


    def initial_value_at_birth(self, new_part_IDs):
        self.set_values(self.params['initial_value'], new_part_IDs) # sets this properties values

    def update(self,active):
        # update decay prop each time step
        age = self.shared_info.classes['particle_properties']['age'].get_values(active)
        val = self.params['initial_value']*np.exp(-np.abs(age) / self.params['decay_time_scale'])
        self.set_values(val,active)
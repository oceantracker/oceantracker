from oceantracker.particle_properties._base_properties import ParticleProperty
import numpy as np

class eDNAdetection(ParticleProperty):

    def __init__(self):
        super().__init__()
        self.add_default_params({'name': 'eDNAdetection','decay_time_scale': 1.*3600*24})

        self.add_default_params({'decay_time_scale_hours': 3.,  # sablella
                                'sample_collector_area': .05**2,  # number of animals shedding dna [1, 10, 100]
                                'retained_sample_size_ml': 100.,  # sabella
                                'detection_limit_copies_per_ml': 0.14})
        self.class_doc(desciption= 'eDNAdetection')


    def initial_value_at_birth(self, new_part_IDs):
        part_prop= self.shared_info.classes['particle_properties']
        depth = part_prop['water_depth'].get(new_part_IDs)

        sampling_volume = abs(depth) * self.params[ 'sample_collector_area']  # depth times area of sampler pulled through full water depth
        retained_sample_size_vol = self.params[ 'retained_sample_size_ml'] * 1.E-6
        initial_conc= self.params['detection_limit_copies_per_ml']*1000 * sampling_volume/retained_sample_size_vol
        self.set_values(initial_conc, new_part_IDs) # sets this properties values

    def update(self,active):
        # update c, ie growth going backwards in time,  prop each time step
        age = self.shared_info.classes['particle_properties']['age'].get_values(active)
        conc = self.params['initial_value']*np.exp( np.abs(age) / abs(self.params['decay_time_scale']))

        self.set_values(conc,active)
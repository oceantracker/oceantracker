from oceantracker.particle_properties._base_particle_properties import ManuallyUpdatedParticleProperty
from oceantracker.util.parameter_checking import ParamValueChecker as PVC

from oceantracker.util.numba_util import njitOT, njitOTparallel, prange
import numpy as np
from oceantracker.shared_info import shared_info as si

class FractionalWaterDepth(ManuallyUpdatedParticleProperty):
    '''
    Calculate the fraction of total water depth from particle's z, ie fraction of depth including tide
    is zero at bottom 1 at sea surface
    '''
    def __init__(self):
        super().__init__()
        self.add_default_params({'time_varying': PVC(True,bool),
                                 'name': PVC('fractional_water_depth', str,doc_str='name used within code and in output'),
                                 'is3D': PVC(False,bool)})

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['tide', 'water_depth'])

    def update(self,n_time_step, time_sec, active):
        part_prop = si.class_roles.particle_properties
        self._get_frac_water_depth(
            part_prop['x'].data,
            part_prop['tide'].data,
            part_prop['water_depth'].data,
            si.settings.minimum_total_water_depth,
            self.data,
            active)

    @staticmethod
    @njitOTparallel
    def _get_frac_water_depth(x,tide, water_depth,minimum_total_water_depth,  frac_water_depth, active):
        for nn in  prange(active.size):
            n = active[nn]
            twd =  abs(tide[n] + water_depth[n])
            if twd >= minimum_total_water_depth:
                frac_water_depth[n] = (water_depth[n]+x[n,2]) / twd
            else:
                frac_water_depth[n] = 0.
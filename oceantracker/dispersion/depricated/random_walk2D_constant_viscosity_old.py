import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.dispersion._base_dispersion import BaseTrajectoryModifer
from numba import njit, types as nbtypes
from oceantracker.util.numba_util import njitOT

from random import normalvariate
from oceantracker.util.numba_util import njitOT
from oceantracker.shared_info import shared_info as si

class RandomWalk2DconstantViscosity(BaseTrajectoryModifer):
    '''
    implements random walk of particles by adding equivalent random velocity
    '''
    def __init__(self):
        # set up default params
        super().__init__()  # required in children to get parent defaults
        self.add_default_params(A_H= PVC(0.1,float,min=0., doc_str='Horizontal turbulent eddy viscosity', units = 'm/s^2'),
                                       )
    def add_required_classes_and_settings(self, settings, known_reader_fields, msg_logger):

        # list of internal names as strings of required non-standard fields to be read from files
        required_reader_fields = []

        # list of parameter dictionary of   custom fields required by this  class to operated,
        # eg spatial field probabity  of where particles are likely to settle on the bottom
        # minumim is  [dict(name='internal naem of feild used to reference it',class_name='class name used to import this custom field'},...]
        # eg is using A_Z profe need custion field of its vertical gradient
        custom_field_params = []

        return required_reader_fields, custom_field_params

    def initial_setup(self):
        info = self.info
        params= self.params
        dt = si.settings.time_step
        info['random_walk_size'] = np.array((self._calc_walk(self.params['A_H'], dt), self._calc_walk(self.params['A_H'], dt)))
        info['random_walk_velocity'] = info['random_walk_size'] / si.settings['time_step']  # velocity equivalent of random walk distance

    def _calc_walk(self, A_turb, dt):
        # this is variance of particle motion in each vector direction,
        # ( factor of 2 would  be 6 , if wanting 3D isotropic variance, rather than its separate effect on 1D components used above)
        return np.sqrt(2. * np.abs(dt) * np.abs(A_turb))

    # apply random walk
    def update(self, n_time_step,time_sec, active):
        # add up 2D/3D diffusion coeff as random walk done using velocity_modifier
        part_prop = si.class_roles.particle_properties
        self._add_random_walk_velocity2D_modifier_constantAZ(self.info['random_walk_velocity'],
                                                    part_prop['velocity_modifier'].data,  active)

    @staticmethod
    @njitOT
    def _add_random_walk_velocity2D_modifier_constantAZ(random_walk_velocity, velocity_modifier, active):
        for n in active:
            for m in range(2):
                velocity_modifier[n,m] += normalvariate(0., random_walk_velocity[m])


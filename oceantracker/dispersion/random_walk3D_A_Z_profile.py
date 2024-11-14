import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.dispersion._base_dispersion import BaseTrajectoryModifer
from oceantracker.dispersion.random_walk3D_constant_viscosity import RandomWalk3DconstantViscosity

from random import normalvariate
from oceantracker.util.numba_util import njitOT
from oceantracker.shared_info import shared_info as si

class RandomWalk3D_A_Z_profile(RandomWalk3DconstantViscosity):
    '''
    implements random walk of particles by adding equivalent random velocity
    '''
    def __init__(self):
        # set up default params
        super().__init__()  # required in children to get parent defaults

    def check_requirements(self):
        if si.settings['use_A_Z_profile']:
                self.check_class_required_fields_prop_etc(requires3D=True,
                                                            required_props_list=['nz_cell', 'x', 'n_cell'],
                                                          crumbs='random walk with use_A_Z_profile')
    def add_any_required_fields(self,settings, known_reader_fields, msg_logger):
        required_reader_fields =['A_Z_profile']
        custom_field_params = [dict(name= 'A_Z_profile_vertical_gradient',
                                    class_name = 'VerticalGradient',
                                    get_grad_of_field_named='A_Z_profile',
                                    write_interp_particle_prop_to_tracks_file=False)]
        return required_reader_fields, custom_field_params



    def initial_setup(self):
        info = self.info
        params= self.params
        dt = si.settings.time_step
        info['random_walk_size'] = np.array((self._calc_walk(self.params['A_H'], dt), self._calc_walk(self.params['A_H'], dt)))
        info['random_walk_velocity'] = info['random_walk_size'] / si.settings['time_step']  # velocity equivalent of random walk distance

    # apply random walk
    def update(self, n_time_step,time_sec, active):
        # add up 2D/3D diffusion coeff as random walk done using velocity_modifier
        part_prop = si.class_roles.particle_properties
        self._add_random_walk_velocity_modifier(part_prop['A_Z_profile'].data, part_prop['A_Z_profile_vertical_gradient'].data,
                                                self.info['random_walk_velocity'],
                                                np.abs(si.settings.time_step),
                                                active, part_prop['velocity_modifier'].data)

    @staticmethod
    @njitOT
    def _add_random_walk_velocity_modifier(A_Z,A_Z_vertical_gradient,random_walk_velocity,timestep, active, velocity_modifier):
        # add vertical advection effect of dispersion to random walk, see Lynch Particles in the Coastal Ocean: Theory and Applications
        # this avoids particle accumulating in areas of high vertical gradient of A_Z, ie top and bottom

        for n in active:
            # random walk velocity in horizontal
            for m in range(2):
                velocity_modifier[n,m] += normalvariate(0., random_walk_velocity[m])

            # pseudo-advection required by random walk to avoid accumulation
            velocity_modifier[n, 2] += A_Z_vertical_gradient[n]  # todo limit excursion by this velocity ?

            # random walk in vertical
            random_walk_size= np.sqrt(2. * timestep * np.abs(A_Z[n]))
            velocity_modifier[n, 2] += normalvariate(0.,  random_walk_size/timestep) # apply vertical walk as a velocity


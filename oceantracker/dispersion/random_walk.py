import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.dispersion._base_dispersion import BaseTrajectoryModifer
from numba import njit, types as nbtypes
from oceantracker.util.numba_util import njitOT

from random import normalvariate
from oceantracker.util.numba_util import njitOT
from oceantracker.shared_info import shared_info as si

class RandomWalk(BaseTrajectoryModifer):
    '''
    implements random walk of particles by adding equivalent random velocity
    '''
    def __init__(self):
        # set up default params
        super().__init__()  # required in children to get parent defaults
        self.add_default_params(A_H= PVC(0.1,float,min=0., doc_str='Horizontal turbulent eddy viscosity', units = 'm/s^2'),
                                A_V= PVC(0.01,float,min=0., doc_str='Constant vertical turbulent eddy viscosity', units = 'm/s^2'),
                                       )

    def check_requirements(self):
        if si.settings['use_A_Z_profile']:
                self.check_class_required_fields_prop_etc(requires3D=True,
                                                            required_props_list=['nz_cell', 'x', 'n_cell'],
                                                          crumbs='random walk with use_A_Z_profile')
    def add_any_required_fields(self,settings, known_reader_fields, msg_logger):
        info = self.info

        if settings['use_A_Z_profile'] and 'A_Z_profile' in known_reader_fields:
            self.add_required_reader_field('A_Z_profile')  # set up reading from file
            self.add_required_custom_field('A_Z_profile_vertical_gradient','VerticalGradient',  msg_logger,
                                            params=dict(name_of_field='A_Z_profile', write_interp_particle_prop_to_tracks_file=False),
                                           crumbs='random walk > Adding A_Z_vertical_gradient field, for using_AZ_profile')
    def initial_setup(self):
        info = self.info
        params= self.params
        dt = si.settings.time_step
        info['random_walk_size'] = np.array((self._calc_walk(self.params['A_H'], dt), self._calc_walk(self.params['A_H'], dt), self._calc_walk(self.params['A_V'], dt)))
        if not si.run_info.is3D_run:
            info['random_walk_size'] = info['random_walk_size'][:2]

        info['random_walk_velocity'] = info['random_walk_size'] / si.settings['time_step']  # velocity equivalent of random walk distance

        # detect of using A_Z_profile
        info['use_A_Z_profile'] = 'A_Z_profile' in si.core_class_roles.field_group_manager.fields

    def _calc_walk(self, A_turb, dt):
        # this is variance of particle motion in each vector direction,
        # ( factor of 2 would  be 6 , if wanting 3D isotropic variance, rather than its separate effect on 1D components used above)
        return np.sqrt(2. * np.abs(dt) * np.abs(A_turb))

    # apply random walk
    def update(self, n_time_step,time_sec, active):
        # add up 2D/3D diffusion coeff as random walk done using velocity_modifier
        part_prop = si.class_roles.particle_properties

        if  si.run_info.is3D_run:
            if  self.info['use_A_Z_profile']:
                # hindcast has A_Z profile
                self._add_random_walk_velocity_modifier(part_prop['A_Z_profile'].data, part_prop['A_Z_profile_vertical_gradient'].data,
                                                        self.info['random_walk_velocity'],
                                                        np.abs(si.settings.time_step),
                                                        active, part_prop['velocity_modifier'].data)
            else:
                # constant vertical A_V
                self._add_random_walk_velocity3D_modifier_constantAZ(self.info['random_walk_velocity'],
                                                                 active, part_prop['velocity_modifier'].data )
        else:
            # 2D
            self._add_random_walk_velocity2D_modifier_constantAZ(self.info['random_walk_velocity'],
                                                                     active, part_prop['velocity_modifier'].data)

    @staticmethod
    @njitOT
    def _add_random_walk_velocity2D_modifier_constantAZ(random_walk_velocity, active, velocity_modifier):
        for n in active:
            for m in range(2):
                velocity_modifier[n,m] += normalvariate(0., random_walk_velocity[m])

    @staticmethod
    @njitOT
    def _add_random_walk_velocity3D_modifier_constantAZ(random_walk_velocity, active, velocity_modifier):
        for n in active:
            for m in range(3):
                velocity_modifier[n,m] += normalvariate(0., random_walk_velocity[m])

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


from random import normalvariate
from numba import njit, types as nbtypes
from oceantracker.dispersion.random_walk import RandomWalk
#from oceantracker.interpolator.util.scatch_tests.vertical_walk_at_particle_location_eval_interp import _evalBCinterp
import numpy as np

class RandomWalkVaryingAZ(RandomWalk):
    # dispersion for PDE of  the form d(A_z d(V)/dz)/dz if turbulent eddy viscosity A_z depends on z adds  vertical advection to random walk equal to d A_z/dz
    # see Lynch Particles in the Coastal Ocean: Theory and Applications
    def __init__(self):
        # set up default params
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({ } )


    def initial_setup(self):
        super().initial_setup()
        si=self.shared_info
        pgm = si.classes['particle_group_manager']

        si.msg_logger.msg('RandomWalkVaryingAz: varying Az adds vertical velocity to dispersion to avoid particle accumulation at surface and bottom, ensure time step is small enough that vertical displacement is a small fraction of the water depth, ie vertical Courant number < 1',warning=True)

    def check_requirements(self):
       self.check_class_required_fields_prop_etc(required_fields_list=['A_Z','A_Z_vertical_gradient'],
                                                             requires3D=True,
                                                             required_props_list=['A_Z','A_Z_vertical_gradient','nz_cell', 'x', 'n_cell'])
    # apply random walk
    def update(self, time_sec, active):
        # add up 2D/3D diffusion coeff as random walk vector, plus vertical advection given by
        si= self.shared_info
        prop = si.classes['particle_properties']
        self._add_random_walk_velocity_modifier(prop['A_Z'].data, prop['A_Z_vertical_gradient'].data,
                                                self.info['random_walk_velocity'],
                                                np.abs(si.settings['time_step']),
                                                active, prop['velocity_modifier'].data)

    @staticmethod
    @njit()
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






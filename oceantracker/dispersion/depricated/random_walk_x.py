import numpy as np
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from oceantracker.dispersion._base_dispersion import _BaseTrajectoryModifer
from numba import njit, guvectorize, int32, int64, float64

class RandomWalk(_BaseTrajectoryModifer):
    # add random walk using x displacement
    def __init__(self):
        # set up default params
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC('random_walk',str),'A_H': PVC(1.0,float,min=0.), 'A_V': PVC(0.001,float,min=0.), } )

    def initialize(self):
        si=self.shared_info
        info= self.info
        # get time step from solver
        dt = si.model_substep_timestep

        info['random_walk_size'] = np.array((self.calc_walk(self.params['A_H'], dt), self.calc_walk(self.params['A_H'], dt), self.calc_walk(self.params['A_V'], dt)))
        if not si.hydro_model_is3D:
            info['random_walk_size'] =  info['random_walk_size'][:2]

        # set up shortcut to data required to modify velocity  below
        info['random_velocity_size'] = info['random_walk_size']/dt
        self.random_velocity = info['random_velocity_size']

    def calc_walk(self, A_turb, dt):
        # this is variance of particle motion in each vector direction,
        # ( factor of 2 would  be 6 , if wanting 3D isotropic variance, rather than its separate effect on 1D components used above)
        return np.sqrt(2. * np.abs(dt) * np.abs(A_turb))

    # apply random walk
    def update(self,nb,  time, active):
        # add up 2D/3D diffusion coeff as random walk vector
        si= self.shared_info
        self._add_random_walk_velocity(self.random_velocity, active,si.classes['particle_properties']['velocity_modifier'].data)

    @staticmethod
    @njit(fastmath=True)
    #@guvectorize([(float64[:],int32[:],float64[:,:])],' (m), (l)->(n,m)') #, does not work needs n on LHS
    def _add_random_walk_velocity(random_velocity_size, active, velocity_modifier):
        for n in active:
            for m in range(velocity_modifier.shape[1]):
                # todo below slow? is allcating memory??, try math.random random.Genetaor.normal  and get 2-3 at same time above
                velocity_modifier[n,m] += random_velocity_size[m]* np.random.randn()
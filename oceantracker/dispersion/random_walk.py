import numpy as np
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from oceantracker.dispersion._base_dispersion import BaseTrajectoryModifer


class RandomWalk(BaseTrajectoryModifer):

    def __init__(self):
        # set up default params
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC('random_walk',str),'A_H': PVC(1.0,float,min=0.), 'A_V': PVC(0.001,float,min=0.), } )

    def initialize(self):
        si=self.shared_info
        info= self.info
        # get time step from solver
        dt = si.model_substep_timestep

        if si.hindcast_is3D: #3D
            info['rx'] = np.array((self.calc_walk(self.params['A_H'],dt),self.calc_walk(self.params['A_H'],dt),self.calc_walk(self.params['A_V'],dt)))
        else:# 2D
            info['rx']  = np.array((self.calc_walk(self.params['A_H'], dt), self.calc_walk(self.params['A_H'], dt) ))

        # set up shortcut to data requried to modify velocity  below      eg.
        self.rx = info['rx']

    def calc_walk(self, A_turb, dt):
        # this is variance of particle motion in each vector direction,
        # ( factor of 2 would  be 6 , if wanting 3D isotropic variance, rather than its separate effect on 1D components used above)
        return np.sqrt(2. * np.abs(dt) * np.abs(A_turb))

    # apply random walk
    def update(self,nb,  time, active):
        # add up 2D/3D diffusion coeff as random walk vector
        prop_x= self.shared_info.classes['particle_properties']['x']

        prop_x.add_values_to(np.random.randn(active.shape[0], prop_x.num_vector_dimensions()) * self.rx, active)
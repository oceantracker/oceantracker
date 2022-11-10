import numpy as np

from numba import njit
from oceantracker.dispersion.random_walk import RandomWalk
from oceantracker.interpolator.util.dev.vertical_walk_at_particle_location_eval_interp import _evalBCinterp

class RandomWalkVaryingAz(RandomWalk):
    # dispersion for PDE of  the form d(A_z d(V)/dz)/dz if turbulent eddy viscosity A_z depends on z adds  vertical advection to random walk equal to d A_z/dz
    # see Lynch Particles in the Coastal Ocean: Theory and Applications
    def __init__(self):
        # set up default params
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({ } )


    def initialize(self):
        si=self.shared_info
        super().initialize()
        si.case_log.write_warning('RandomWalkVaryingAz: varying Az adds vertical velocity to dispersion, ensure time step is small enough that vertical displacement is a small fraction of the water depth, ie vertical Courant number < 1')

    def check_requirements(self):
        msg_list = self.check_class_required_fields_list_properties_grid_vars_and_3D(required_fields_list=['turbulent_vertical_eddy_viscosity','nz_cell','x','n_cell'],
                                                                                requires3D=True, required_props_list='turbulent_vertical_eddy_viscosity')
        return msg_list

    # apply random walk
    def update(self,nb,  time, active):
        # add up 2D/3D diffusion coeff as random walk vector
        t
        si= self.shared_info
        prop = si.classes['particle_properties']
        fields= si.classes['fields']
        self._add_random_walk(prop['x'].data,
                              si.grid['zlevel'][nb, :, :],
                              prop['n_cell'],
                              prop['nz_cell'],
                              si.grid['tiangles'],
                              fields['turbulent_vertical_eddy_viscosity'].data[nb, :, :],
                              fields['turbulent_vertical_eddy_viscosity'].data[nb, :, :],
                              si.model_substep_timestep,
                              t_fraction,
                              self.rx, active)

    @staticmethod
    @njit(fastmath=True)
    def _add_random_walk(x, z_level, n_cell, nz_nodes, tri, A_z1,A, dt, rx, bc_cords, active):
        # add vertical advection effect of dispersion to random walk, see Lynch Particles in the Coastal Ocean: Theory and Applications
        gradAz_nodes=np.full((3,), 0.)
        vertVel_Az = np.full((1,), 0.)

        for n in active:

            # random walk in horizontal
            for m in range(2):
                x[n,m] += rx[m]*np.random.randn()


            # if linear interp in vertical so gradient Az constant within a zlevel, so dont need vertical interplation
            for m in range(3):
                node = tri[n_cell[n],m]
                nz = nz_nodes[n,m]
                dz= z_level[node, nz + 1] - z_level[node, nz]
                if dz > 1.0E-3:
                    gradAz_nodes[m] = (A_z[node, nz + 1] - A_z[node, nz]) / dz
                else:
                    gradAz_nodes[m] = 0.

            # take nodal values and get gradient at particle location
            _evalBCinterp(bc_cords[n, :], gradAz_nodes, vertVel_Az)

            dz_w = vertVel_Az[0]*dt
            dz_random = rx[2]*np.random.randn()

            # limit size of advection as Az may be so large that dz_z is greater than water depth
            # limit to 2 sigma times random walk as advection
            if np.abs(dz_w) < 2.0*rx[2]:
                dz= dz_random + dz_w
            else:
                dz = dz_random + 2.0*rx[2]*np.sign(dz_w)

            # add random walk in the vertical
            x[n,2] += dz





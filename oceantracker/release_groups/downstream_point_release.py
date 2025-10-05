import numpy as np
from copy import deepcopy

from oceantracker.util.parameter_checking import (
    ParamValueChecker as PVC,
    ParameterCoordsChecker as PCC,
)
from oceantracker.release_groups.point_release import PointRelease
from oceantracker.shared_info import shared_info as si


class DownstreamPointRelease(PointRelease):
    """
    Release particles 10 meter downstream of given points.
    Takes downstream direction water_velocity at release time from hydromodel.
    """

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params(
            {
                "downstream_distance": PVC(
                    None,  # initial value
                    float,  # data type
                    min=0.0,
                    doc_str="Particles are released from a 'downstream' locations of each point.",
                    units="Meters, unless hydro-model coords are in (lon,lat) then distance must be given in degrees",
                ),
            },
        )
        info = self.info
        info["release_type"] = "downstream_point"

    def get_hori_release_locations(self, time_sec):
        # get a unit vector pointing downstream at each release location
        downstream_vector = self._get_downstream_vector(time_sec)
        # do things

        rg = super().get_hori_release_locations(time_sec)
        return rg

    def _get_downstream_vector(self, time_sec):
        """
        Fetch velocity vectors at each release location for the given time.
        Returns: ndarray of shape (n_points, 2) for (u, v) at each point.
        """
        # Get release locations (coordinates) on the xy plane
        release_locations_xy = self.release_info["x"]
        # Get the vertical location
        release_locations_z


        

        # Get time step index of previous and next hindast time step i.e. buffer
        velocity = self.hydro_model.get_velocity_at_points(coords, time_sec)
        # velocity: shape (n_points, 2) for (u, v)

        # Normalize to get unit downstream vectors
        norm = np.linalg.norm(velocity, axis=1, keepdims=True)
        downstream_vector = np.divide(
            velocity, norm, out=np.zeros_like(velocity), where=norm != 0
        )

        return downstream_vector


# @njitOTparallel
def time_dependent_3D_vector_field_data_in_all_layers(
    n_buffer,
    fractional_time_steps,
    F_data,
    triangles,
    n_cell,
    bc_coords,
    nz_cell,
    z_fraction,
    F_out,
    active,
):
    #  time dependent 3D linear interpolation in place, ie write directly to F_out for isActive particles

    # create views to remove redundant dim at current and next time step, improves speed?
    F1 = F_data[n_buffer[0], :, :, :]
    F2 = F_data[n_buffer[1], :, :, :]
    frac0, frac1 = fractional_time_steps[0], fractional_time_steps[1]

    # loop over active particles and vector components
    for nn in nb.prange(active.size):
        n = active[nn]
        zf2 = z_fraction[n]
        zf1 = 1.0 - zf2
        nz = nz_cell[n]

        # loop over each vertex in triangle
        for c in range(3):
            F_out[n, c] = 0.0  # zero out for summing

        for m in range(3):
            # loop vertex of tri
            node = triangles[n_cell[n], m]
            for c in range(3):
                # add contributions from layer above and below particle, for each spatial component at two time steps
                # slightly faster with temp variable, as allows more LLVM optimisations?
                temp = (F1[node, nz, c] * zf1 + F1[node, nz + 1, c] * zf2) * frac0
                temp += (
                    F2[node, nz, c] * zf1 + F2[node, nz + 1, c] * zf2
                ) * frac1  # second time step
                F_out[n, c] += bc_coords[n, m] * temp

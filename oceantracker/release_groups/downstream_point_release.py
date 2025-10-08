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

    # from _base_release_group.py:
    # def get_release_locations(self, time_sec):
    #     info = self.info
    #     release_info= self.get_hori_release_locations(time_sec)

    #     if si.run_info.is3D_run:
    #         self._add_vertical_release(release_info)

    #     info['pulseID'] += 1
    #     info['number_released'] += release_info['x'].shape[0]  # count number released in this group

    #     return release_info
    
    def get_release_locations(self, time_sec):
        """
        Overrides default method to first find normal horizontal release location
        and vertical location, then adjust horizontal location to be downstream
        of original point by the specified distance.
        """
        info = self.info
        release_info= self.get_hori_release_locations(time_sec)

        if si.run_info.is3D_run:
            ml = si.msg_logger
            ml.msg('Downstream Point Release used the surface velocity only for the time being',warning=True)
            release_info = self._add_vertical_release(release_info)

        release_info = self.move_hori_release_locations_downstream(release_info, time_sec, self.params['downstream_distance'])

        # do i need to do this here?
        # # apply user filter
        # use_points = self.user_release_point_filter(release_info, time_sec=time_sec)
        # release_info = self._retain_release_locations(release_info, use_points)
        # <<<<<<<<< copy from _apply_dry_cell_[...] in _base_release_group.py
        

        

        info['pulseID'] += 1
        info['number_released'] += release_info['x'].shape[0]  # count number released in this group

        return release_info
    
    def move_hori_release_locations_downstream(self, release_info, time_sec, distance):
        # get a unit vector pointing downstream at each release location
        fgm = self.si.core_class_roles.field_group_manager
        interpolator = self.si.core_class_roles.reader.interpolator

        downstream_vector_norm = self._get_downstream_vector(self.release_info, time_sec)

        release_locations_xy = release_info['x'][:, :2]  # only horizontal part
        new_release_locations_xy = release_locations_xy + downstream_vector_norm * distance

        release_info['x'][:, :2] = new_release_locations_xy 
        
        return release_info

    def _get_downstream_vector(self, release_info, time_sec):
        """
        Fetch velocity vectors at each release location for the given time.
        Returns: ndarray of shape (n_points, 2) for (u, v) at each point.
        """
        fgm = si.core_class_roles.field_group_manager
       
        # if no z coord is provided, we use the surface value
        # depth averaged would proabably be better but more complex to implement
        nz_cell = np.full((release_info['x'].shape[0]),-1,dtype=np.int32)
        z_fraction = np.zeros((release_info['x'].shape[0]),dtype=np.float32)

        release_info['water_velocity'] = (
            fgm.interp_named_3D_vector_fields_at_given_locations_and_time(
                field_name='water_velocity', 
                x=release_info['x'],
                n_cell=release_info['n_cell'],
                bc_coords=release_info['bc_coords'],
                nz_cell=nz_cell,
                z_fraction=z_fraction,
                time_sec=time_sec,
                hydro_model_gridID=release_info['hydro_model_gridID']
                )
        )
        horiz_velocity = release_info['water_velocity'][:, :2]  # only need horizontal part

        # Normalize to get unit downstream vectors
        norm = np.linalg.norm(horiz_velocity, axis=1, keepdims=True)
        downstream_vector = np.divide(horiz_velocity, norm, where=norm != 0)

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

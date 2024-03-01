from numba import njit
from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier
from oceantracker.util.numba_util import njitOT
from oceantracker.common_info_default_param_dict_templates import particle_info

# globals
status_stranded_by_tide = int(particle_info['status_flags']['stranded_by_tide'])
status_stationary = int(particle_info['status_flags']['stationary'])
status_moving = int(particle_info['status_flags']['moving'])

class TidalStranding(_BaseTrajectoryModifier):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({})

    def check_requirements(self):
        si = self.shared_info
        self.check_class_required_fields_prop_etc()


    def update(self,grid, time_sec,sel):
        si=self.shared_info
        part_prop  =  si.classes['particle_properties']

        tidal_stranding_from_dry_cell_index(
            grid['dry_cell_index'],
            part_prop['n_cell'].data,
            sel,
            part_prop['status'].data)
        pass


@njitOT
def tidal_stranding_from_dry_cell_index(dry_cell_index, n_cell, sel, status):
    # look at all particles in buffer to check total water depth < water_depth_min
    #  use  0-255 dry cell index updated at each interpolation update
    for n in sel:
        if status[n] >= status_stationary:

            if dry_cell_index[n_cell[n]] > 128: # more than 50% dry
                status[n] = status_stranded_by_tide

            elif status[n] == status_stranded_by_tide:
                # unstrand if already stranded, if status is on bottom,  remains as is
                status[n] = status_moving
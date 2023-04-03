from numba import njit
from oceantracker.status_modifiers._base_status_modifers import _BaseStatusModifer

from oceantracker.common_info_default_param_dict_templates import particle_info
# globals
status_stranded_by_tide = int(particle_info['status_flags']['stranded_by_tide'])
status_frozen = int(particle_info['status_flags']['frozen'])
status_moving = int(particle_info['status_flags']['moving'])

class TidalStranding(_BaseStatusModifer):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({})

    def check_requirements(self):
        si = self.shared_info
        self.check_class_required_fields_prop_etc(required_grid_time_buffers_var_list=['dry_cell_index'])


    def update(self, time_sec,sel):
        si=self.shared_info
        part_prop  =  si.classes['particle_properties']

        tidal_stranding_from_dry_cell_index(
            si.classes['reader'].grid_time_buffers['dry_cell_index'],
            part_prop['n_cell'].data,
            sel,
            part_prop['status'].data)
        pass


@njit
def tidal_stranding_from_dry_cell_index(dry_cell_index, n_cell, sel, status):
    # look at all particles in buffer to check total water depth < min_water_depth
    #  use  0-255 dry cell index updated at each interpolation update
    for n in sel:
        if status[n] >= status_frozen:

            if dry_cell_index[n_cell[n]] > 128: # more than 50% dry
                status[n] = status_stranded_by_tide

            elif status[n] == status_stranded_by_tide:
                # unstrand if already stranded, if status is on bottom,  remains as is
                status[n] = status_moving
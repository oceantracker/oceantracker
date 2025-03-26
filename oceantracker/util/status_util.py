from oceantracker.shared_info import shared_info as si
import numpy as np
def build_select_status_map(status_list):
    # all false except where 100+ integer status values named in list are True
    # input is names of status's as strings, eg ['moving','dead']
    # used to screen status value operations

    if len(status_list)==0:
        # selct those >=0 if not list given
        status_list = si.particle_status_flags.possible_values()

    a = np.full((si.particle_status_flags.moving - si.particle_status_flags.unknown +1,),
                False,dtype=bool)

    status_dict = si.particle_status_flags.asdict()
    for s in status_list:
        a[status_dict[s]-si.particle_status_flags.unknown]= True
    return a

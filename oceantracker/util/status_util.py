from oceantracker.shared_info import shared_info as si
import numpy as np
def build_select_status_map(status_list):
    # all false except where 100+ integer status values named in list are True
    # input is names of status's as strings, eg ['moving','dead']
    # used to screen status value operations

    if len(status_list)==0:
        # selct those >=0 if not list given
        status_list = [key for key,val in  si.particle_status_flags.as_dict().items() if val >=0 ]

    a = np.full((128,),False,dtype=bool)
    for s in status_list:
        a[100 + si.particle_status_flags[s]]= True
    return a

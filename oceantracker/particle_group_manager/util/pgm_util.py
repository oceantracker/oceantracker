import soupsieve
from numba import  njit

from oceantracker.util.numba_util import njitOT
from oceantracker.shared_info import shared_info as si

status_stationary = int(si.particle_status_flags.stationary)
status_dead = int(si.particle_status_flags.dead)

@njitOT
def _status_counts_and_kill_old_particles(age, status, IDrelease_group,max_age_for_each_release_group,status_counts,num_in_buffer):
    # fast way to kill off old particles, bactracking?
    for m in range(status_counts.size): status_counts[m] = 0
    num_alive = 0
    # loop over active buffer
    for n in range(num_in_buffer):
        if status[n] >= status_stationary and abs(age[n]) > max_age_for_each_release_group[IDrelease_group[n]] :
            status[n] =  status_dead

        # add to histogram of status values
        status_counts[status[n] - 128] += 1
        if status[n] >= status_stationary:
            num_alive += 1

    return num_alive

status_stationary = int(si.particle_status_flags.stationary)
status_moving = int(si.particle_status_flags.moving)
@njitOT
def _find_status_alive(status,out):
    nfound = 0
    for n in range(status.size):
        if status[n] >= status_stationary:
            out[nfound] = n
            nfound += 1
    return out[:nfound]

@njitOT
def _find_status_moving(status, out):
    nfound = 0
    for n in range(status.size):
        if status[n] == status_moving:
            out[nfound] = n
            nfound += 1
    return out[:nfound]
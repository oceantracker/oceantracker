from oceantracker.util.numba_util import njitOT, njitOTparallel
from numba import prange, get_thread_id, get_num_threads
from oceantracker.shared_info import shared_info as si


# status counting, of finding moving or stationary
status_outside_open_boundary = int(si.particle_status_flags.outside_open_boundary)
status_dead = int(si.particle_status_flags.dead)
status_moving = int(si.particle_status_flags.moving)
status_on_bottom = int(si.particle_status_flags.on_bottom)
status_stranded_by_tide = int(si.particle_status_flags.stranded_by_tide)

@njitOTparallel
def _status_counts_and_kill_old_particles(age, status, IDrelease_group,max_age_for_each_release_group,
                status_count_array_per_thread,num_in_buffer):

    for n in range(status_count_array_per_thread.shape[0]):
        for m in range(status_count_array_per_thread.shape[1]): status_count_array_per_thread[n,m] = 0

    alive = 0
    # loop over active buffer
    for n in prange(num_in_buffer):
        is_active = status[n] >= status_outside_open_boundary

        # kill particles older than their release groups max age
        if is_active and abs(age[n]) > max_age_for_each_release_group[IDrelease_group[n]] :
            status[n] =  status_dead
            is_active = False

        alive += is_active
        status_count_array_per_thread[get_thread_id(),int(status[n]) - status_outside_open_boundary] += 1

    return alive

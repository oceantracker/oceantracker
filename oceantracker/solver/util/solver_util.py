from numba import njit

@njit
def euler_substep(xnew, xold, velocity, dt, active):
    # do euler substep, xnew = xold+velocity*dt for active particles
    for n in active:
        for m in range(xold.shape[1]):
            xnew[n, m] = xold[n, m] + velocity[n, m] * dt


@njit
def tidal_stranding_from_dry_cell_index(dry_cell_index, n_cell, status_frozen, status_stranded ,status_moving, sel, status):
    # look at all particles in buffer to check total water depth < min_water_depth
    #  use  0-255 dry cell index updated at each interpolation update
    for n in sel:
        if status[n] >= status_frozen:

            if dry_cell_index[n_cell[n]] > 128: # more than 50% dry
                status[n] = status_stranded

            elif status[n] == status_stranded:
                # unstrand if already stranded, if status is on bottom,  remains as is
                status[n] = status_moving



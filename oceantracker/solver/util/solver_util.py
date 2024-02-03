from numba import njit, types as nbt
from oceantracker.util.numba_util import njitOT
@njitOT(nbt.void(nbt.float64[:,:], nbt.float64[:,:], nbt.float64[:,:], nbt.float64, nbt.int32[:], nbt.float64[:,:]))
def euler_substep(xold, water_velocity, velocity_modifier, dt, active, xnew):
    # do euler substep, xnew = xold+ (velocity+velocity_modifier) *dt for active particles
    for n in active:
        for m in range(xnew.shape[1]):#todo faster to have separate 2D and 3D versions with number of componets fixed at 2 or 3
            xnew[n, m] = xold[n, m] + (water_velocity[n, m] + velocity_modifier[n, m]) * dt






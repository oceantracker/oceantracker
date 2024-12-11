from numba import njit, types as nbt
from oceantracker.util.numba_util import njitOT
#@njitOT(nbt.void(nbt.float64[:,:], nbt.float64[:,:], nbt.float64[:,:], nbt.float64, nbt.int32[:], nbt.float64[:,:]))
@njitOT
def euler_substep2D(xold, water_velocity, velocity_modifier, dt, active, xnew):
    # do euler substep, xnew = xold+ (velocity+velocity_modifier) *dt for active particles
    for n in active:
        for m in range(2):# faster to have separate 2D and 3D versions with number of componets fixed at 2 or 3
            xnew[n, m] = xold[n, m] + (water_velocity[n, m] + velocity_modifier[n, m]) * dt
@njitOT
def euler_substep3D(xold, water_velocity, velocity_modifier, dt, active, xnew):
    # do euler substep, xnew = xold+ (velocity+velocity_modifier) *dt for active particles
    for n in active:
        for m in range(3):# faster to have separate 2D and 3D versions with number of componets fixed at 2 or 3
            xnew[n, m] = xold[n, m] + (water_velocity[n, m] + velocity_modifier[n, m]) * dt

#@njitOT(nbt.void(nbt.float64[:,:],nbt.float64[:,:], nbt.float64[:,:], nbt.float64[:,:], nbt.float64, nbt.int32[:], nbt.float64[:,:]))
@njitOT
def euler_substep_geographic2D(degrees_per_meter, xold, water_velocity, velocity_modifier, dt, active, xnew):
    # do euler substep, xnew = xold+ (velocity+velocity_modifier) *dt for active particles
    for n in active:
        for m in range(2):# faster to have separate 2D and 3D versions with number of componets fixed at 2 or 3
            xnew[n, m] = xold[n, m] + (water_velocity[n, m] + velocity_modifier[n, m]) * dt * degrees_per_meter[n,m]

@njitOT
def euler_substep_geographic3D(degrees_per_meter, xold, water_velocity, velocity_modifier, dt, active, xnew):
    # do euler substep, xnew = xold+ (velocity+velocity_modifier) *dt for active particles
    for n in active:
        for m in range(2):# faster to have separate 2D and 3D versions with number of componets fixed at 2 or 3
            xnew[n, m] = xold[n, m] + (water_velocity[n, m] + velocity_modifier[n, m]) * dt * degrees_per_meter[n,m]
        xnew[n, 2] = xold[n, 2] + (water_velocity[n, 2] + velocity_modifier[n, 2]) * dt



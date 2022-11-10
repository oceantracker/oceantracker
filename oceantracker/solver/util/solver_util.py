from numba import njit, float64, int32, guvectorize

#@njit()
# experiment with guvectorize, guvectorize 40-50% faster than njit,  parallel  no faster as too small an operation, ?
@guvectorize([(float64[:,:], float64[:,:],float64[:,:], float64, int32[:],float64[:,:])], '(n,m),(n,m),(n,m),(),(l)->(n,m)')
#@guvectorize([(float64[:,:], float64[:,:],float64[:,:], float64, int32[:],float64[:,:])], '(n,m),(n,m),(n,m),(),(l)->(n,m)',target='parallel')
def euler_substep(xold, water_velocity, velocity_modifier, dt, active, xnew):
    # do euler substep, xnew = xold+velocity*dt for active particles
    for n in active:
        for m in range(water_velocity.shape[1]):
            xnew[n, m] = xold[n, m] + (water_velocity[n, m] + velocity_modifier[n, m]) * dt






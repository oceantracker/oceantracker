from numba import  njit , prange ,types as nbt
import numpy as np
from oceantracker.interpolator.util import triangle_interpolator_util as tri_interp_util
from oceantracker.interpolator.util import eval_interp

#@njit(parallel = True, nogil=True)
@njit()
def RKsolver(time_sec,vel_field, grid, part_prop, interp_step_info, ksi, time_step,RK_order,  active):
    # integrated interploated hydro model
    # and any velocity_modifier applied, eg terminal velocity , random walk

    # below does
    #   v = (v1 + 2.0 * (v2 + v3) + v4) /6
    #  x2 = x1 +  v*dt

    st= interp_step_info
    velocity_modifier = part_prop['velocity_modifier']
    n_dims = part_prop['x'].shape[1]

    # substep velocity and locations
    # RK solve  for eack particle
    for nn in prange(active.size): # make prange soon!
        n = active[nn]

        x0 = part_prop['x'][n, :]
        vm = velocity_modifier[n, :]
        eval_water_velocity(x0, time_sec, vel_field, grid, part_prop, st, ksi['bc'], n, ksi['v1'])
        if RK_order == 1:
            euler_substep(x0, ksi['v1'],vm , time_step, part_prop['x'][n, :])
            continue

        # RK2  half step
        euler_substep(x0, ksi['v1'], vm, time_step / 2.0, ksi['x_temp'])
        eval_water_velocity(ksi['x_temp'], time_sec, vel_field, grid, part_prop, st, ksi['bc'], n, ksi['v2'])
        if RK_order == 2:
            euler_substep(x0, ksi['v2'], vm, time_step, ksi['x_temp'])
            continue

        #RK 3
        euler_substep(x0, ksi['v2'], vm, time_step / 2.0, ksi['x_temp'])
        eval_water_velocity(ksi['x_temp'], time_sec, vel_field, grid, part_prop, st, ksi['bc'], n, ksi['v3'])

        # RK 4 full step
        euler_substep(x0, ksi['v3'], vm, time_step, ksi['x_temp'])
        eval_water_velocity(ksi['x_temp'], time_sec, vel_field, grid, part_prop, st, ksi['bc'], n, ksi['v4'])

        # put results together
        for m in range(n_dims): ksi['v'][m] =ksi['v1'][m] + 2.0 * ksi['v2'][m] + 2.0 * ksi['v3'][m] + ksi['v4'][m]
        euler_substep(x0, ksi['v']/6.0, vm, time_step,  part_prop['x'][n, :])

@njit()
def eval_water_velocity(xq, time_sec,vel_field, grid, part_prop, st, bc,  n, v_out) :
    # evaluate water velocity for single particle, after cell search

    # set buffer index from this time and next inside stepinfo
    # todo this could be done 2-4 times at begining for sub set times not for every particle and subsep??
    tri_interp_util.set_hindcast_buffer_steps(time_sec, st)
    time_hindcast = grid['time'][st['nb'][0]]

    # update fractions of time step
    tri_interp_util.set_time_fractions(time_sec, time_hindcast, st)

    # find cell for xq, node list and weight for interp at calls
    # then evaluate velocity
    tri_interp_util._kernal_BCwalk_with_move_backs(xq, grid, part_prop, n, st, bc)

    if st['is_3D_run']:
        # vertical walk
        tri_interp_util._kernal_get_depth_cell_time_varying_Slayer(xq, grid, part_prop, st, n)
        eval_interp._kernal_eval_water_velocity_3D(v_out, vel_field, grid, part_prop, st, n)
    else:
        eval_interp._kernal_time_dependent_2Dfield(v_out, vel_field, grid, part_prop, st, n)

@njit(nbt.void(nbt.float64[:],nbt.float64[:],nbt.float64[:],nbt.float64,nbt.float64[:]))
def euler_substep(xold, water_velocity, velocity_modifier, dt, xnew):
    # do euler substep, xnew = xold+ (velocity+velocity_modifier) *dt for active particles
    for m in range(xnew.shape[0]):
        xnew[m] = xold[m] + (water_velocity[m] + velocity_modifier[m]) * dt

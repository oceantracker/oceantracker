from numba import njit

#todo faster with signature!
#todo make it work faster on vectors, gufunc???, ie
@njit
def kernal_linear_interp1D(x1, y1, x2, y2, x):
    # linearly interpolate  to location x between (x1,y1), (x2,y2))
    dx = x2-x1
    if abs(dx) > 1.0E-6:
        f = (x - x1) / dx
    else:
        f = 0.
    return  y1 +  f * (y2-y1)
from numba import njit

#todo add signature
#todo make it work on vectors???, ie
@njit
def kernal_linear_interp1D(x1, y1, x2, y2, x):
    # liner interpolate  to location x between (x1,y1), (x2,y2))
    dx = x2-x1
    if abs(dx) > 1.0E-6:
        f = (x - x1) / dx
    else:
        f = 0.
    return  y1 +  f * (y2-y1)
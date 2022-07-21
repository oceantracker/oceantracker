
# line intersection
# see Computer Graphics by F.stats_parent. Hill
# https://stackoverflow.com/questions/3252194/numpy-and-line-intersections
import numpy  as np
def perp( a ) :
    b = np.empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b

# line segment a given by endpoints a1, a2
# line segment b given by endpoints b1, b2
# return
def seg_intersect(a1,a2, b1,b2) :
    da = a2-a1
    db = b2-b1
    dp = a1-b1
    dap = perp(da)
    denom = np.dot( dap, db)
    num = np.dot( dap, dp )
    return (num / denom.astype(float))*db + b1, denom, num
'''
p1 = array( [0.0, 0.0] )
p2 = array( [1.0, 0.0] )

p3 = array( [4.0, -5.0] )
p4 = array( [4.0, 2.0] )

print seg_intersect( p1,p2, p3,p4)

'''


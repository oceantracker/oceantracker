import matplotlib.pyplot as plt
#import matplotlib.patches as patches
#from matplotlib import gridspec
from numba import njit, types as nbtypes
#from  matplotlib import nxutils
from matplotlib import path
import numpy as np
import time
import copy

class InsidePolygon(object):
    # finds points inside given polygon (M,2) vertices as numpy array
    # may be a closed or not closed polygon
    def __init__(self,verticies):
        self.points = self._make_closed(verticies).astype(np.float64) # close  polygon if needed
        self._pre_calc_bounds_of_polygon(self.points)
        self.inside_ray_tracing_indices = make_inside_ray_tracing_indices(self.line_bounds, self.slope_inv, self.polygon_bounds,)

    def is_inside(self, xq,  out = None):
        # returns vector of booleans if each point in (N,2) numpy array of points


        # guard against single xq as [x,y], not [[x,y]]
        if xq.size ==2 and xq.ndim ==1:  xq = xq.reshape((-1,2))

        if out is None: out = np.zeros((xq.shape[0],), bool)

        b = inside_ray_tracing_boolean(xq, self.line_bounds, self.slope_inv, self.polygon_bounds, out)
        return b

    def inside_indices(self, xq, active=None, out = None, also_return_indices_outside = False, out_outside=None):
        # returns vector of indices for each point in (N,2) numpy array of points
        # for only isActive particles

        # guard against single xq as [x,y], needs to be  [[x,y]]
        if xq.size ==2 and xq.ndim ==1: xq = xq.reshape((-1,2))

        if out is None:  out = np.zeros((xq.shape[0],), dtype=np.int32)

        if also_return_indices_outside:
            if out_outside is None:  out_outside = np.zeros((xq.shape[0],), dtype=np.int32)
        else:
            out_outside = np.zeros((1,), dtype=np.int32)  # allows numba code to compile and tesl it not to return indices of thsoe outside

        if active is None:  active = np.arange(xq.shape[0]) # search all xq for those inside

        active = active.astype(np.int32) # ensure its int32
        # get tuple of found and not found
        indices = self.inside_ray_tracing_indices(xq,  active, out, out_outside)

        if also_return_indices_outside:
            return indices # return both  those inside and outside
        else: # only return those found
            return indices[0]

    def _pre_calc_bounds_of_polygon(self, vert):
        # build set of bounding boxes for each line of polygon
        # recalculates inv_slope for intersection calc and bounding box
        # assumes a closed polygon
        nv=vert.shape[0]
        self.line_bounds = np.zeros((nv,3,2),dtype=np.float64)
        xyb= np.zeros((2,2),dtype=np.float64)
        self.slope_inv = np.zeros((nv,),dtype=np.float64)
        for n in range(nv-1):
            xy =vert[ [n,  (n+1) % nv ],:]   # cords of this line
            xyb[:, 0] = np.sort(xy[:, 0])
            xyb[:, 1] = np.sort(xy[:, 1])
            self.line_bounds[n,:2,:] = copy.copy(xyb)

            # slope, line origin  must come from unordered line
            if xy[1,1] != xy[0,1]:
                self.slope_inv[n] = (xy[1,0] - xy[0,0])/(xy[1,1] - xy[0,1])

            # start of line , used with intercept to find intersections
            self.line_bounds[n,2, :] = xy[0, :].astype(np.float64)

        self.polygon_bounds = np.array([np.min(vert[:,0]), np.max(vert[:,0]),
                         np.min(vert[:,1]),  np.max(vert[:,1]) ])

    def _make_closed(self, p):
        # inside works whether closed or not, but ensure a closed polygon unless requested
        if np.any(p[0,:] != p[-1,:]):
            p= np.vstack((p,p[0,:]))
        return p

    def _get_area(self):
        # area of closed polygon, by planimeter method?
        #todo move to own utility, use triangle util?
        xy=self.points
        xy0  = self.points[0,:]
        a = 0
        for n in range(xy.shape[0]):
            a += (xy[n,0] * xy0[1] - xy[n,1] * xy0[0])
        return abs(a / 2)

@njit
def inside_ray_tracing_boolean(xq, lb, slope_inv, bounds, out):
    # finds if points inside polygon based on ray from point to +ve x
    # based on odd number of crossings of lines of polygon, result is a boolean working space, "inside"

    for n in range(xq.shape[0]):
        out[n]= inside_ray_tracing_single_point(xq[n,:], lb, slope_inv, bounds)

    return  out

def make_inside_ray_tracing_indices(lb, slope_inv, bounds):
    # wrapper to make faster reduce number of arguments anf faster by compling fixed array references into code

    @njit(nbtypes.UniTuple(nbtypes.int32[:],2)(nbtypes.float64[:,:], nbtypes.int32[:], nbtypes.int32[:], nbtypes.int32[:]))
    #@njit()
    def inside_ray_tracing_indices(xq, active, inside_IDs, outside_IDs):
        # finds if points indside polygon based on ray from point to +ve x
        # based on odd number of crossings of lines of polygon, resilt is in boolean working space, "inside"
        # this version returns the indices of those inside,  in first n_found values of index buffer
        # if outside.shape[0] > 1 then those outside are also put in outside buffer

        n_inside = 0
        n_outside= 0

        for n in active:
            inside = inside_ray_tracing_single_point(xq[n, :], lb, slope_inv, bounds)

            if inside :
                # add to index list if inside
                inside_IDs[n_inside] = n
                n_inside += 1

            elif outside_IDs.shape[0] > 1:
                # only insert not found if outside_IDs is given as full size
                outside_IDs[n_outside] = n
                n_outside +=1

        return inside_IDs[:n_inside], outside_IDs[:n_outside]

    return inside_ray_tracing_indices

@njit()
def inside_ray_tracing_single_point(xq, lb, slope_inv, bounds):
    # finds if a single point is inside polygon based on ray from point to +ve x

    xints = 0
    inside = False
    if bounds[0] <=  xq[0] <= bounds[1] and bounds[2] <= xq[1] <= bounds[3]:  # inside bounds of polygon
        for i in range(lb.shape[0]):
            # get line's bounding box, faster to do this in one line tuple assignment
            p1x, p1y, p2x, p2y = lb[i, 0, 0], lb[i, 0, 1], lb[i, 1, 0], lb[i, 1, 1]
            if p1y < xq[1] <= p2y:
                if  xq[0] <= p2x:
                    if p1y != p2y:
                        xints = (xq[1] - lb[i, 2, 1]) * slope_inv[i] + lb[i, 2, 0]
                    if p1x == p2x or xq[0] <= xints:
                        inside = not inside

    return inside

def set_up_list_of_polygon_instances(polygon_list):
    msg=[]
    polygons=[]
    for n, poly in enumerate(polygon_list):

        a = np.asarray(poly['points'])

        p = InsidePolygon(verticies=a)  # do set up to speed inside using pre-calculation
        polygons.append(p)

        # ensure points closure updates parameters
        poly.update({'points': p.points.tolist()})
    return polygons, msg

if __name__ == '__main__':

    N=10**5
    x=30*np.hstack( (np.random.rand(N,1),-np.random.rand(N,1) )) +np.array([[-5,7]])

    v = np.array([[5.5      , -5],
                  [  5.11      , -10.00907385],
                  [  5.11      , -14.68307385],
                  [  6.89      , -14.68307385],
                  [ 10    , -10.00907385],
                  [0, -8],
                  [ 5      , 3]
                  ])

    active = np.sort(np.flatnonzero(np.random.rand(N) > 0.1))
    out = np.zeros((N,), dtype=np.int32)

    # speed tests
    P= InsidePolygon(v)

    nrepeats = 10000

    t0=time.time()

    P.inside_indices(x[:3,:],out = out)

    for n in range(nrepeats):
        indices_inside = P.inside_indices(x,active=active, out= out)
    print('indicies inside', time.time() - t0, nrepeats*N/10**6)


    # test plots
    xtest = x[::20,:]
    indices_inside = P.inside_indices(xtest)
    # check index and boolean agree
    indices_inside_check = np.flatnonzero(P.is_inside(xtest))
    if indices_inside.size > 0:
        print('compare', np.max(np.abs(indices_inside-indices_inside_check)))
    else:
        print('no points')
    plt.plot(v[:, 0], v[:, 1], 'k-', markersize=10, )
    plt.plot(P.points[:, 0], P.points[:, 1], 'k--', markersize=10, )
    plt.plot(xtest[:,0],xtest[:,1],'x',markersize=3,color=[1,0,0])
    plt.plot(xtest[indices_inside, 0], xtest[indices_inside, 1], '.', markersize=4, color=[0, 1, 0])

    plt.show()


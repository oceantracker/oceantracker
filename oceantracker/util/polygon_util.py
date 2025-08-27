#import matplotlib.patches as patches
#from matplotlib import gridspec
from numba import njit, types as nbtypes
#from  matplotlib import nxutils
import numpy as np
import time
import copy
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange
from oceantracker.util import cord_transforms

class InsidePolygon(object):
    # finds points inside given polygon (M,2) vertices as numpy array
    # may be a closed or not closed polygon
    def __init__(self,verticies,geographic_coords=None):
        self.geographic_coords = geographic_coords
        self.points = self._make_closed(verticies).astype(np.float64) # close  polygon if needed
        self._pred_calcs(self.points)


    def is_inside(self, xq,  out = None):
        # returns vector of booleans if each point in (N,2) numpy array of points
        # guard against single xq as [x,y], not [[x,y]]
        if xq.size ==2 and xq.ndim ==1:  xq = xq.reshape((-1,2))

        index= self.inside_indices(xq)
        b= np.zeros((xq.shape[0],),dtype=bool)
        b[index] =True
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
        indices = self.inside_ray_tracing_indices(xq,
                                                  self.line_bounds, self.slope_inv, self.polygon_bounds,
                                                  active, out, out_outside)

        if also_return_indices_outside:
            return indices # return both  those inside and outside
        else: # only return those found
            return indices[0]

    def _pred_calcs(self, vert):
        # do precalulations require to build a function to find indicies of points inside a polygon
        # 1) build set of bounding boxes for each line of polygon
        # 2) recalculates inv_slope for intersection calc and bounding box
        # assumes a closed polygon

        self.line_bounds, self.slope_inv = self._get_line_bounds_and_slopeinv(vert )

        self.polygon_bounds = np.array([np.min(vert[:,0]), np.max(vert[:,0]),
                                       np.min(vert[:,1]),  np.max(vert[:,1]) ])
    @staticmethod
    @njitOT
    def _get_line_bounds_and_slopeinv(vert):
        nv = vert.shape[0]
        line_bounds = np.zeros((nv, 3, 2), dtype=np.float64)
        slope_inv = np.zeros((nv,), dtype=np.float64)
        xyb = np.zeros((2, 2), dtype=np.float64)
        xy = xyb.copy()
        for n in range(nv - 1):
            # cords of this line segment
            xy[0,:]= vert[n,:]
            xy[1,:]= vert[(n + 1) % nv,:]
            # sort to get bounds of segment lower left and upper right
            xyb[:, 0] = np.sort(xy[:, 0])
            xyb[:, 1] = np.sort(xy[:, 1])
            line_bounds[n, :2, :] = xyb.copy()

            # slope, line origin  must come from unordered line
            if xy[1, 1] != xy[0, 1]:
                slope_inv[n] = (xy[1, 0] - xy[0, 0]) / (xy[1, 1] - xy[0, 1])

            # start of line , used with intercept to find intersections
            line_bounds[n, 2, :] = xy[0, :].astype(np.float64)
        return  line_bounds, slope_inv

    def _make_closed(self, p):
        # inside works whether closed or not, but ensure a closed polygon unless requested
        if np.any(p[0,:] != p[-1,:]):
            p= np.vstack((p,p[0,:]))
        return p

    def get_area(self):
        # area of  closed polygon, by planimeter method?
        #   if geographic_coords must be small ie a couple of degrees in longtitude geographically small
        # ie inside one UTM zone

        xy=self.points
        if self.geographic_coords:
            xy =  cord_transforms.WGS84_to_UTM(xy, in_lat_lon_order=False)

        x,y = xy[:,0], xy[:,1]
        return self._get_area_numba(x,y)

    @staticmethod
    @njitOT
    def _get_area_numba(x,y):
        n = len(x)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += x[i] * y[j]
            area -= x[j] * y[i]

        area = abs(area) / 2.0
        return area

    @staticmethod
    @njitOT
    def inside_ray_tracing_indices(xq_vals,lb, slope_inv, bounds, active, inside_IDs, outside_IDs):
        # finds if points indside polygon based on ray from point to +ve x
        # based on odd number of crossings of lines of polygon, resilt is in boolean working space, "inside"
        # this version returns the indices of those inside,  in first n_found values of index buffer
        # if outside.shape[0] > 1 then those outside are also put in outside buffer

        n_inside = 0
        n_outside= 0

        for n in active:
            xq= xq_vals[n,: ]
            xints = 0
            inside = False
            if bounds[0] <= xq[0] <= bounds[1] and bounds[2] <= xq[1] <= bounds[3]:  # inside bounds of polygon
                for i in range(lb.shape[0]):
                    # get line's bounding box, faster to do this in one line tuple assignment
                    p1x, p1y, p2x, p2y = lb[i, 0, 0], lb[i, 0, 1], lb[i, 1, 0], lb[i, 1, 1]
                    if p1y < xq[1] <= p2y:
                        if xq[0] <= p2x:
                            if p1y != p2y:
                                xints = (xq[1] - lb[i, 2, 1]) * slope_inv[i] + lb[i, 2, 0]
                            if p1x == p2x or xq[0] <= xints:
                                inside = not inside
            if inside :
                # add to index list if inside
                inside_IDs[n_inside] = n
                n_inside += 1

            elif outside_IDs.shape[0] > 1:
                # only insert not found if outside_IDs is given as full size
                outside_IDs[n_outside] = n
                n_outside +=1

        return inside_IDs[:n_inside], outside_IDs[:n_outside]



def set_up_list_of_polygon_instances(polygon_list,geographic_coords=False):
    msg=[]
    polygons=[]
    for n, poly in enumerate(polygon_list):

        a = np.asarray(poly['points'])

        p = InsidePolygon(verticies=a,geographic_coords=geographic_coords)  # do set up to speed inside using pre-calculation
        polygons.append(p)

        # ensure points closure updates parameters
        poly.update({'points': p.points.tolist()})
    return polygons, msg



def make_anticlockwise_polygon(xy):
    # ensure points in polygon are ordered in anti-clockwise order
    is_clockwise = np.sum(np.arctan2( xy[:,0],xy[:,1]  ),axis=0) > 0
    if ~is_clockwise:
        xy = xy [::-1,:]
    return xy


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    N=10**6


    v = np.array([[5.5      , -5],
                  [  5.11      , -10.00907385],
                  [  5.11      , -14.68307385],
                  [  6.89      , -14.68307385],
                  [ 10    , -10.00907385],
                  [0, -8],
                  [ -1      , 3]
                  ])
    dx =.5
    bounds = [np.min(v[:,0]) -dx, np.max(v[:,0]) +dx, np.min(v[:,1]) -dx, np.max(v[:,1]) +dx]
    x = np.stack(((np.random.rand(N, )-.5)*np.diff(bounds[:2]), (np.random.rand(N, )-.5)*np.diff(bounds[2:])),axis=1) + np.mean(v,axis=0)

    active = np.sort(np.flatnonzero(np.random.rand(N) > 0.1))
    out = np.zeros((N,), dtype=np.int32)

    # speed tests
    P= InsidePolygon(v)

    nrepeats = 10
    P.inside_indices(x[:3, :], out=out)
    t0=time.time()

    for n in range(nrepeats):
        indices_inside = P.inside_indices(x,active=active, out= out)
    print('indicies inside', time.time() - t0, nrepeats*N/10**6,'million points checked')


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


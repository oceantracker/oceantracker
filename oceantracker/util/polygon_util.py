#import matplotlib.patches as patches
#from matplotlib import gridspec
from numba import njit, types as nbtypes
#from  matplotlib import nxutils
import numpy as np
import time
import copy
from oceantracker.util.numba_util import njitOT


class InsidePolygon(object):
    # finds points inside given polygon (M,2) vertices as numpy array
    # may be a closed or not closed polygon
    def __init__(self,verticies, bounds_sub_grid_size=20):
        self.points = self._make_closed(verticies).astype(np.float64) # close  polygon if needed
        self._build_inside_indicies_func(self.points, bounds_sub_grid_size)

        # build number function wrapped in precalc data as constants
        self._build_inside_indicies_func(self.points, bounds_sub_grid_size)

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
        indices = self.inside_ray_tracing_indices_fun(xq,  active, out, out_outside)

        if also_return_indices_outside:
            return indices # return both  those inside and outside
        else: # only return those found
            return indices[0]

    def _build_inside_indicies_func(self, vert, bounds_sub_grid_size):
        # do precalulations require to build a function to find indicies of points inside a polygon
        # 1) build set of bounding boxes for each line of polygon
        # 2) recalculates inv_slope for intersection calc and bounding box
        # 3) form subgrid of bounding region with vaules =1 if polygon overlays  subgrid cell
        # assumes a closed polygon
        #todo this can be much faster with numba?
        nv = vert.shape[0]
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

        # make an initial function to find id points inside with one subcell
        x = np.linspace(self.polygon_bounds[0], self.polygon_bounds[1], 2)
        y = np.linspace(self.polygon_bounds[2], self.polygon_bounds[3],  2)
        overlap = np.ones((1, 1), dtype=np.int8)
        self.inside_ray_tracing_indices_fun = make_inside_ray_tracing_indices(self.line_bounds, self.slope_inv, self.polygon_bounds,
                                                            x,y,overlap)

        # set up sub-grid of bounds to speed eliminating points from full check for ray tracing
        x = np.linspace(self.polygon_bounds[0], self.polygon_bounds[1], bounds_sub_grid_size + 1)
        y = np.linspace(self.polygon_bounds[2], self.polygon_bounds[3], bounds_sub_grid_size + 1) # break symetry to test
        overlap = np.zeros((y.size-1, x.size-1), dtype=np.int8)

        # check if any of 4 corners of each cell is inside polygon
        for r in np.arange(y.size - 1):
            for c in np.arange(x.size-1):
                xq = np.asarray([[x[c],y[r]],[x[c+1],y[r]],[x[c+1],y[r+1]],[x[c],y[r+1]]])
                corner_inside_polygon = np.any(self.is_inside(xq))
                vertex_inside_sub_grid = False
                for p in self.points:

                    if x[c] <= p[0] <= x[c+1] and y[r] <= p[1] <= y[r+1]:
                        vertex_inside_sub_grid = True
                        break # stop if any vertex inside the rectangle
                        
                overlap[r,c] = corner_inside_polygon or vertex_inside_sub_grid


        # setup sub grid info and  find inside_ray_tracing_indices_fun  which exploits the sub grid
        self.sub_grid_x = x
        self.sub_grid_y = y
        self.sub_grid_overlaps_polygon = overlap
        self.inside_ray_tracing_indices_fun = make_inside_ray_tracing_indices(self.line_bounds, self.slope_inv, self.polygon_bounds,
                                                                     self.sub_grid_x, self.sub_grid_y, self.sub_grid_overlaps_polygon)
        pass

    def _make_closed(self, p):
        # inside works whether closed or not, but ensure a closed polygon unless requested
        if np.any(p[0,:] != p[-1,:]):
            p= np.vstack((p,p[0,:]))
        return p

    def get_area(self):
        # area of closed polygon, by planimeter method?
        #todo move to own utility, use triangle util?
        x, y=self.points[:,0], self.points[:,1]
        n = len(x)
        area = 0.0

        for i in range(n):
            j = (i + 1) % n
            area += x[i] * y[j]
            area -= x[j] * y[i]

        area = abs(area) / 2.0
        return area

def make_inside_ray_tracing_indices(lb, slope_inv, bounds,sub_grid_x,sub_grid_y, sub_grid_overlaps_polygon):
    # wrapper to make faster reduce number of arguments anf faster by compling fixed array references into code

    # useful constants
    sub_grid_dx = sub_grid_x[1] - sub_grid_x[0]
    sub_grid_dy = sub_grid_y[1] - sub_grid_y[0]

    @njit
    def inside_ray_tracing_indices(xq_vals, active, inside_IDs, outside_IDs):
        # finds if points indside polygon based on ray from point to +ve x
        # based on odd number of crossings of lines of polygon, resilt is in boolean working space, "inside"
        # this version returns the indices of those inside,  in first n_found values of index buffer
        # if outside.shape[0] > 1 then those outside are also put in outside buffer

        n_inside = 0
        n_outside= 0
        r_lims = sub_grid_overlaps_polygon.shape[0]-1
        c_lims = sub_grid_overlaps_polygon.shape[1]-1

        for n in active:
            xq= xq_vals[n,: ]
            xints = 0
            inside = False
            if bounds[0] <= xq[0] <= bounds[1] and bounds[2] <= xq[1] <= bounds[3]:  # inside bounds of polygon
                # check if point in subgrid cell overlaping the polygon
                c , r = int((xq[0]-sub_grid_x[0])/sub_grid_dx), int((xq[1]-sub_grid_y[0])/sub_grid_dy)
                # only look at polygon if subcell does not overlap polygon
                #  also make sure point on edge of bounds round down
                if sub_grid_overlaps_polygon[min(r, r_lims), min(c, c_lims)] == 1:
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

    return inside_ray_tracing_indices

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
    import matplotlib.pyplot as plt
    N=10**4


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
    P= InsidePolygon(v,bounds_sub_grid_size = 20)

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

    x, y = np.meshgrid(P.sub_grid_x, P.sub_grid_y)
    plt.plot(x,y,c=[.8,.8,.8])
    plt.plot(x.T, y.T, c=[.8, .8, .8])
    plt.plot(v[:, 0], v[:, 1], 'k-', markersize=10, )
    plt.plot(P.points[:, 0], P.points[:, 1], 'k--', markersize=10, )
    plt.plot(xtest[:,0],xtest[:,1],'x',markersize=3,color=[1,0,0])
    plt.plot(xtest[indices_inside, 0], xtest[indices_inside, 1], '.', markersize=4, color=[0, 1, 0])

    x,y = np.meshgrid(P.sub_grid_x,P.sub_grid_y)
    x = .5*(x[:-1,:-1]+x[1:,1:])
    y = .5 * (y[:-1, :-1] + y[1:, 1:])
    sel=P.sub_grid_overlaps_polygon ==0
    plt.scatter(x[sel],y[sel],marker='x', c='k', s=8)

    plt.show()


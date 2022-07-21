import matplotlib.pyplot as plt
#import matplotlib.patches as patches
#from matplotlib import gridspec
from numba import njit
#from  matplotlib import nxutils
from matplotlib import path
import numpy as np
import time
import copy

class InsidePolygon(object):
    # finds points inside given polygon (M,2) vertices as numpy array
    # may be a closed or not closed polygon
    def __init__(self,verticies):
        self.points = self.make_closed(verticies).astype(np.float64) # close  polygon if needed
        self.pre_calc_bounds_of_polygon(self.points)

    def is_inside(self, xq,  out = None, active = None):
        # returns vector of booleans if each point in (N,2) numpy array of points
        # sel only proceses id numbers in sel

        # guard against single xq as [x,y], not [[x,y]]
        if xq.size ==2 and xq.ndim ==1:  xq = xq.reshape((-1,2))

        if out is None: out = np.full((xq.shape[0],), False, bool)


        if active is None: active = np.arange(xq.shape[0])

        self.inside_ray_tracing(xq, self.line_bounds, self.slope_inv, self.polygon_bounds, out, active)

        # return a view of output buffer
        return out[:xq.shape[0]]

    def inside_indices(self, xq, active=None, out = None, also_return_indices_outside = False, out_outside=None):
        # returns vector of indices for each point in (N,2) numpy array of points
        # for only isActive particles

        # guard against single xq as [x,y], needs to be  [[x,y]]
        if xq.size ==2 and xq.ndim ==1: xq = xq.reshape((-1,2))

        if out is None:  out = np.full((xq.shape[0],), 0)

        if also_return_indices_outside:
            if out_outside is None:  out_outside = np.full((xq.shape[0],), 0)
        else:
            out_outside = np.full((1,), 0)  # allows numba code to compile and tesl it not to return indices of thsoe outside

        if active is None:  active = np.arange(xq.shape[0]) # search all xq for those inside

        # get tuple of found and not found
        indices = self.inside_ray_tracing_indices(xq, self.line_bounds, self.slope_inv, self.polygon_bounds, active, out, out_outside)

        if also_return_indices_outside:
            return indices # return both  those inside and outside
        else: # only return those found
            return indices[0]

    def pre_calc_bounds_of_polygon(self, vert):
        # build set of bounding boxes for each line of polygon
        # recalculates inv_slope for intersection calc and bounding box
        # assumes a closed polygon
        nv=vert.shape[0]
        self.line_bounds = np.full((nv,3,2), 0.)
        xyb= np.zeros((2,2))
        self.slope_inv = np.full((nv,), 0.)
        for n in range(nv-1):
            xy =vert[ [n,  (n+1) % nv ],:]   # cords of this line
            xyb[:, 0] = np.sort(xy[:, 0])
            xyb[:, 1] = np.sort(xy[:, 1])
            self.line_bounds[n,:2,:] =copy.copy(xyb)

            # slope, line origin  must come from unordered line
            if xy[1,1] != xy[0,1]:
                self.slope_inv[n] = (xy[1,0] - xy[0,0])/(xy[1,1] - xy[0,1])

            # start of line , used with intercept to find intersections
            self.line_bounds[n,2, :] = xy[0, :]

        self.polygon_bounds = np.array([np.min(vert[:,0]), np.max(vert[:,0]),
                         np.min(vert[:,1]),  np.max(vert[:,1]) ])

    def make_closed(self, p):
        # inside works whether closed or not, but ensure a closed polygon unless requested
        if np.any(p[0,:] != p[-1,:]):
            p= np.vstack((p,p[0,:]))
        return p

    def get_area(self):
        # area of closed polygon, by planimeter method?

        xy=self.points
        xy0  = self.points[0,:]
        a = 0
        for n in range(xy.shape[0]):
            a += (xy[n,0] * xy0[1] - xy[n,1] * xy0[0])
        return abs(a / 2)



    @staticmethod
    @njit
    def inside_ray_tracing(xq, lb, slope_inv, bounds, inside,active):
        # finds if points indsde poygon based on ray from point to +ve x
        # based on odd number of crossings of lines of polygon, result is a boolean working space, "inside"

        nlines = lb.shape[0]
        b1, b2, b3, b4 = bounds

        for n in active:
            x = xq[n,0]
            y = xq[n,1]
            inside[n]= False
            xints = 0
            if b1 <= x <= b2 and b3 <= y <= b4: # check if inside bounds of polygon
                for i in range(nlines):
                    # get line bounding box, faster to do this in one line tuple assignment
                    p1x, p1y, p2x, p2y = lb[i, 0, 0], lb[i, 0, 1],lb[i, 1, 0], lb[i, 1, 1]

                    if p1y < y <= p2y :
                        if x <= p2x:
                            if p1y != p2y:
                                xints = (y -  lb[i, 2, 1]) * slope_inv[i]  + lb[i, 2, 0]
                            if p1x == p2x or x <= xints :
                                inside[n] = not inside[n]  # why not just say true

    @staticmethod
    @njit
    def inside_ray_tracing_indices(xq, lb, slope_inv, bounds, active, inside_IDs, outside_IDs):
        # finds if points indsde poygon based on ray from point to +ve x
        # based on odd number of crossings of lines of polygon, resilt is in boolean working space, "inside"
        # this version returns the indices of those inside,  in first n_found values of index buffer
        # if outside.shape[0] > 1 then those outside are also put in outside buffer
        nlines = lb.shape[0]
        b1, b2, b3, b4 = bounds
        n_inside = 0
        n_outside= 0

        for n in active:
            x = xq[n, 0]
            y = xq[n, 1]
            xints = 0
            inside = False
            if b1 <= x <= b2 and b3 <= y <= b4:  # inside bounds of polygon
                for i in range(nlines):
                    # get line's bounding box, faster to do this in one line tuple assignment
                    p1x, p1y, p2x, p2y = lb[i, 0, 0], lb[i, 0, 1], lb[i, 1, 0], lb[i, 1, 1]
                    if p1y < y <= p2y:
                        if x <= p2x:
                            if p1y != p2y:
                                xints = (y - lb[i, 2, 1]) * slope_inv[i] + lb[i, 2, 0]
                            if p1x == p2x or x <= xints:
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

    N=10**7
    x=30*np.hstack( (np.random.rand(N,1),- np.random.rand(N,1) )) +np.array([[-5,7]])

    v = np.array([[5.5      , -5],
                  [  5.11      , -10.00907385],
                  [  5.11      , -14.68307385],
                  [  6.89      , -14.68307385],
                  [ 10    , -10.00907385],
                  [0, -8],
                  [ 5      , 3]
                  ])

    xtest=np.array([(4.068793828501192, -9.654343178017031)])
    selR = np.full((x.shape[0],),False)

    P= InsidePolygon(v)
    P.is_inside(xtest)# precompile

    t0=time.time()
    P.is_inside(x,out = selR)
    print('ray',time.time()-t0)

    indices_inside = P.inside_indices(x)
    plt.plot(v[:, 0], v[:, 1], 'k-', markersize=10, )
    plt.plot(P.points[:, 0], P.points[:, 1], 'k--', markersize=10, )

    sel=np.random.rand(N) > 0.999
    plt.plot(x[sel,0],x[sel,1],'.',markersize=2,color=[1,0,0])

    sel2= sel & selR
    plt.plot(x[sel2,0],x[sel2,1],'.',markersize=4,color=[0,1,0])

    plt.plot(x[indices_inside, 0], x[indices_inside, 1], 'x', markersize=4, color=[0, 1, 0])

    # version 2
    P= InsidePolygon(v)
    P.is_inside(xtest) # precompile
    t0=time.time()
    P.is_inside(x, out = selR)
    print('ray',time.time()-t0)

    sel2= sel & selR
    plt.plot(x[sel2,0],x[sel2,1],'.',markersize=2,color=[0,0,1])

    for n in range(v.shape[0]):
        plt.text(v[n,0],v[n,1],str(n))

    plt.plot(xtest[0,0],xtest[0,1],'o',markersize=10)
    print(plt.ginput())
    plt.show()


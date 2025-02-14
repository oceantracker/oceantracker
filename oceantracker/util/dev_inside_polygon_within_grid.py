import numpy as np
from time import  perf_counter
import copy
from oceantracker.util.numba_util import njitOT
from oceantracker.util import cord_transforms
from oceantracker.util import polygon_util, triangle_utilities
from scipy.spatial import cKDTree
from oceantracker.interpolator.util import find_initial_cell

class InsidePolygonWithinGrid(object):
    # finds points inside given polygon (M,2) vertices as numpy array
    # may be a closed or not closed polygon
    def __init__(self,x_polygon, grid, bc_walk_tol=0.001,  geographic_coords=None):
        # from domain grid build a sub triangular grid spanning polygon to do search with its KDtree

        self.bc_walk_tol= bc_walk_tol
        self.geographic_coords = geographic_coords

        # make a inside polygon finder to use only if needed
        self._inside_polygon = polygon_util.InsidePolygon(x_polygon, geographic_coords=geographic_coords)

        # find triangls overlappred by polygon
        domain_tri = grid['triangles']
        node_inside_polygon = np.full_like(domain_tri,False,dtype=bool)
        for n in range(3):
            x_node= grid['x'][domain_tri[:,n],:2]
            node_inside_polygon[:, n] =  self._inside_polygon.is_inside(x_node)
        tri_overlaps = np.any(node_inside_polygon, axis=1)



        # make triangulation for subgrid from domain triangulation
        # first make a map from domain tri to subgrid tri
        sub_grid_tri = domain_tri[tri_overlaps, :]
        sub_grid_nodes = np.unique(sub_grid_tri)

        m = np.full((domain_tri.size,),-1,dtype=np.int32)
        m[sub_grid_nodes] = np.arange(sub_grid_nodes.size) # insert new node numbers into

        sub_grid = dict( x = grid['x'][sub_grid_nodes,:],
                         triangles =  m[sub_grid_tri])

        sub_grid['node_to_tri_map'], sub_grid['tri_per_node'] =  triangle_utilities.build_node_to_triangle_map(sub_grid['triangles'], sub_grid['x'])
        self.subgrid = sub_grid
        pass

    def is_inside(self, xq, n_domain_cell = None,  out = None):
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

        # make an initial function to find if points inside with one subcell
        x = np.linspace(self.polygon_bounds[0], self.polygon_bounds[1], 2)
        y = np.linspace(self.polygon_bounds[2], self.polygon_bounds[3],  2)
        overlap = np.ones((1, 1), dtype=np.int8)
        self.inside_ray_tracing_indices_fun = self.make_inside_ray_tracing_indices_subgrids(self.line_bounds, self.slope_inv, self.polygon_bounds,
                                                                                       x, y, overlap)

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
        self.inside_ray_tracing_indices_fun = self.make_inside_ray_tracing_indices_subgrids(self.line_bounds, self.slope_inv, self.polygon_bounds,
                                                                                       self.sub_grid_x, self.sub_grid_y, self.sub_grid_overlaps_polygon)
        pass

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
        n = len(x)
        area = 0.0

        for i in range(n):
            j = (i + 1) % n
            area += x[i] * y[j]
            area -= x[j] * y[i]

        area = abs(area) / 2.0
        return area

    @staticmethod
    def make_inside_ray_tracing_indices_subgrids(lb, slope_inv, bounds, sub_grid_x, sub_grid_y, sub_grid_overlaps_polygon):
        # wrapper to make faster reduce number of arguments anf faster by compling fixed array references into code

        # useful constants
        sub_grid_dx = sub_grid_x[1] - sub_grid_x[0]
        sub_grid_dy = sub_grid_y[1] - sub_grid_y[0]

        @njitOT
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




if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import xarray as xr
    from oceantracker.util.ncdf_util import NetCDFhandler


    fn =r'F:\H_Local_drive\ParticleTracking\oceantracker_output\unit_tests\unit_test_01_check-against-ref_00\unit_test_01_check-against-ref_00_grid000.nc'
    fn=r'D:\OceanTrackerOutput\OceanTrackerProfiling\Sounds\Sounds_grid000.nc'

    nc = NetCDFhandler(fn)
    grid= nc.read_variables()



    x_polygon = [[1597682.1237, 5489972.7479],
                 [1598604.1667, 5490275.5488],
                 [1598886.4247, 5489464.0424],
                 [1597917.3387, 5487000],
                 [1597300, 5487000],
                 [1597682.1237, 5489972.7479]]

    x_polygon = [[1590000, 5489000],
                 [1598000, 5490000],
                 [1597000, 5480000],
                [1590000, 5475000],
              ]

    x_polygon= np.asarray(x_polygon)


    P= InsidePolygonWithinGrid(x_polygon, grid)



    # make random ponts acros the domain
    N=10**3
    dx = 10000
    bounds = [x_polygon[:,0].min()-dx, x_polygon[:,0].max()+dx,x_polygon[:,1].min()-dx, x_polygon[:,1].max()+dx,]
    x = np.stack((np.random.uniform(low=bounds[0], high=bounds[1], size=(N,)),
                    np.random.uniform(low=bounds[2], high=bounds[3], size=(N,))), axis=1)



    active = np.sort(np.flatnonzero(np.random.rand(N) > 0.1))
    out = np.zeros((N,), dtype=np.int32)

    # speed tests old version
    P= polygon_util.InsidePolygon(x_polygon)
    nrepeats = 10
    P.inside_indices(x[:3, :], out=out)
    t0=perf_counter()
    for n in range(nrepeats):
        indices_inside = P.inside_indices(x,active=active, out= out)
    print('indicies inside', perf_counter() - t0, nrepeats*N/10**6,'million points checked')


    # test plots
    xtest = x[::10000,:]

    # check index and boolean agree
    indices_inside_check = np.flatnonzero(P.is_inside(xtest))



    plt.triplot(xgrid[:,0],xgrid[:,1], tri_grid, c=[.8,.8, .8])
    plt.scatter(x[:,0], x[:,1], s= 2)
    plt.scatter(x[indices_inside, 0], x[indices_inside, 1], s=4, color=[0, 1, 0])

    plt.plot(x_polygon[:, 0], x_polygon[:, 1], c='r')

    #x, y = np.meshgrid(P.sub_grid_x, P.sub_grid_y)
    #plt.plot(x,y,c=[.8,.8,.8])
    #plt.plot(x.T, y.T, c=[.8, .8, .8])
    #plt.plot(x[:, 0], x[:, 1], 'k-', markersize=10, )
    #plt.plot(P.points[:, 0], P.points[:, 1], 'k--', markersize=10, )

    plt.xlim(bounds[0]-dx, bounds[1]+dx)
    plt.ylim(bounds[2]-dx, bounds[3]+dx)
    if False:
        x,y = np.meshgrid(P.sub_grid_x,P.sub_grid_y)
        x = .5*(x[:-1,:-1]+x[1:,1:])
        y = .5 * (y[:-1, :-1] + y[1:, 1:])
        sel=P.sub_grid_overlaps_polygon ==0
        plt.scatter(x[sel],y[sel],marker='x', c='k', s=8)

    plt.show()


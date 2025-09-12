import numpy as np
from scipy.spatial import cKDTree


class InsidePolygonWithinGrid(object):
    # finds points inside given polygon (M,2) vertices as numpy array
    # may be a closed or not closed polygon
    def __init__(self,x_polygon, x, triangles, bc_walk_tol=0.001,  geographic_coords=None):
        # from domain grid build a sub triangular grid spanning polygon to do search with its KDtree

        self.outer_grid = dict(x=x, triangles=triangles)
        self.sub_grid = dict()

        self._inside_polygon = polygon_util.InsidePolygon(x_polygon, geographic_coords=geographic_coords)
        self.x_polygon= self._inside_polygon.points

        self._find_overlaping_tri()
        self._make_sub_grid()

        return
        self.bc_walk_tol= bc_walk_tol
        self.geographic_coords = geographic_coords

        pass


    def _find_overlaping_tri(self):
        # find outer grid triangles overlapped by polygon
        outer_grid = self.outer_grid
        sub_grid = self.sub_grid


        node_inside_polygon = np.full_like(outer_grid['triangles'], False, dtype=bool)
        # loop over ti vertex
        for n in range(3):
            x_node =  outer_grid['x'][outer_grid['triangles'][ :, n],:2]
            node_inside_polygon[:, n] = self._inside_polygon.is_inside(x_node)

        outer_grid['tri_fully_inside'] =  np.all(node_inside_polygon, axis=1)
        outer_grid['tri_overlaps'] = np.any(node_inside_polygon, axis=1) # outer grid cells which overlap part of polygon

        pass

    def _make_sub_grid(self):
        # make a grid from  overlaping outer triangles
        outer_grid = self.outer_grid
        sub_grid = self.sub_grid

        # make triangulation for subgrid from domain triangulation
        # first make a map from domain tri to subgrid tri
        sub_grid['tri_outer_grid_nodes'] = outer_grid['triangles'][outer_grid['tri_overlaps'], :]
        sub_grid['outer_grid_nodes'] = np.unique(sub_grid['tri_outer_grid_nodes'])
        sub_grid['x'] =  outer_grid['x'][sub_grid['outer_grid_nodes'],...]


        m = np.full(( outer_grid['x'].shape[0],), -1, dtype=np.int32)
        m[sub_grid['outer_grid_nodes']] = np.arange( sub_grid['x'].shape[0])  # insert new node numbers into outer grid sized variable
        sub_grid['triangles'] =  m[sub_grid['tri_outer_grid_nodes']]

        # map sub grid tri to tri number in outer grid
        sub_grid['map_to_outer_tri'] = np.flatnonzero(outer_grid['tri_overlaps'])

        # make outer to sub grid map, -1 where cell does not overlap
        outer_grid['map_to_subgrid_tri'] = np.full((outer_grid['triangles'].shape[0],), -1, dtype = np.int32)
        outer_grid['map_to_subgrid_tri'][outer_grid['tri_overlaps']]  = np.arange(sub_grid['triangles'].shape[0])

        sub_grid['KDtree'] = cKDTree(sub_grid['x'], leafsize=10)
        return


if __name__ == '__main__':
    import matplotlib.pyplot as plt
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


    P = InsidePolygonWithinGrid(x_polygon, grid['x'], grid['triangles'])

    from timeit import timeit
    d = cKDTree(P.outer_grid['x'], leafsize=10)
    print('KDtree query outer', timeit(lambda: d.query(P.outer_grid['x']), number=10))
    print('KDtree query subgrid', timeit(lambda : P.sub_grid['KDtree'].query(P.outer_grid['x']), number = 10))

    og = P.outer_grid
    sg = P.sub_grid
    plt.triplot(og['x'][:, 0], og['x'][:, 1], og['triangles'], c=[.8,.8,.8],lw=1)

    plt.triplot(sg['x'][:, 0], sg['x'][:, 1], sg['triangles'], c=[.8,.2,  .2], lw=.5)
    plt.triplot(og['x'][:, 0], og['x'][:, 1], og['triangles'][og['tri_fully_inside'], :], c=[.2,.8,  .2], lw=.5)



    plt.plot(P.x_polygon[:, 0], P.x_polygon[:, 1], c='g')
    #plt.plot(sg['x'][:,0],sg['x'][:,1],'.',c='r')
    #    plt.triplot(sg['x'][:,0],sg['x'][:,1], sg['triangles'],c='b')
    print(P._inside_polygon.polygon_bounds)

    ax= [1586000., 1599000., 5470000., 5499000.]
    plt.xlim(ax[:2])
    plt.ylim(ax[2:])
    plt.show()

    if False:


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


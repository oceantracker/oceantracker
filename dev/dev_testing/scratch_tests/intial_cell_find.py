import numpy as np
from fontTools.qu2cu.qu2cu import namedtuple
from numba import njit
from timeit import timeit
from time import perf_counter


class KDTreeCellFind:
    def __init__(self,x,y, tri, leaf_size=10):
        self.x,self.y, self.tri = x, y,tri
        self._build_tree(x, y, tri,leaf_size)

    def _build_tree(self,x,y,tri,leaf_size):

        xy_tri= np.stack((x[tri], y[tri]),axis=2)
        cellIDs= np.arange(xy_tri.shape[0])
        x_sorted, y_sorted= np.sort(x,axis=0),np.sort(y,axis=0)
        xy_sorted = np.stack((np.sort(x, axis=0), np.sort(y, axis=0)), axis=1)
        # make root node
        self.tree= self._make_node( None, xy_tri, cellIDs,  x_sorted, y_sorted, leaf_size)
        pass

    def _make_node(self,N, xy_tri, cellIDs, x_sorted, y_sorted,leaf_size):

        if N is None:
            N = self._empty_node(0,
                                 bounds= np.asarray([[x_sorted[0],y_sorted[0]],[x_sorted[-1],y_sorted[-1]]]))

        split_dim= N['level'] % 2
        split_dim_size = x_sorted.size if split_dim ==0 else y_sorted.size
        ns = int((split_dim_size -1)/2)
        N['test_current_cells'] = cellIDs.copy() # debug code

        if xy_tri.shape[0] < leaf_size or split_dim_size< 3:
            N['cellIDs'] = cellIDs.copy()
            print(f'leaf : level {N["level"]}, nsplit {ns},split_dim{split_dim},'
                  f' {split_dim_size}, leaves {cellIDs.size}')
            return N

        N['split_val'] =  x_sorted[ns] if split_dim ==0 else y_sorted[ns]

        # find tri inside bounds of left/right split
        bounds_left = N['bounds'].copy()
        bounds_left[1,split_dim] = N['split_val']
        N['left'] = self._empty_node(N['level'] + 1, bounds_left)
        #sel_left =np.any(np.logical_and( bounds_left[0,split_dim] <= xy_tri[:,:,split_dim],
        #                            xy_tri[:,:,split_dim] <=bounds_left[1,split_dim] ),axis=1)
        sel_left =  self._overlaps_cell(xy_tri, bounds_left, split_dim)

        N['left']= self._make_node(N['left'], xy_tri[sel_left,...], cellIDs[sel_left],
                                   x_sorted[:ns] if split_dim ==0 else x_sorted,
                                   y_sorted[:ns] if split_dim ==1 else y_sorted,
                                   leaf_size)
        # right side
        bounds_right =  N['bounds'].copy()
        bounds_right[0, split_dim] = N['split_val']
        sel_right = self._overlaps_cell(xy_tri, bounds_right, split_dim)
        N['right'] = self._empty_node(N['level'] + 1, bounds_right)
        N['right'] = self._make_node(N['right'], xy_tri[sel_right, ...], cellIDs[sel_right],
                                     x_sorted[ns:] if split_dim == 0 else x_sorted,
                                     y_sorted[ns:] if split_dim == 1 else y_sorted,
                                     leaf_size)

        return N

    @staticmethod
    def _overlaps_cell(xy_tri, bounds, split_dim):
        #work out of trianfles overlap box with LL and UR in bounds
        # bounds lower ;eft upper right coords (xmin, ymin), (xmax,ymax)]

        result= np.zeros((xy_tri.shape[0],),dtype=bool)
        # first check if any node inside box
        for n in range(xy_tri.shape[0]):
            for m in range(3):
                inside = bounds[0, split_dim] <= xy_tri[n, m, split_dim] and \
                                xy_tri[n, m, split_dim] <= bounds[1, split_dim]
                if inside:
                    # only need to find one
                    result[n]= True
                    break # m loop
        # second check if any face of triangle spans

        return result


    def _empty_node(self,level,bounds):
         d= dict(level=level,
                 bounds=bounds,
                 split_val=None,
                 left=None,
                 right=None,
                 cellIDs=None
                     )
         return d


    def _plot_tree(self,level):
        import matplotlib.pyplot as plt

        N = self.tree
        while N['level'] <= level and N['left'] is not None:
            plt.triplot(self.x, self.y, self.tri,c=[0.8,0.8,0.8])
            bounds =N['bounds']
            xy = np.asarray([bounds[0],[bounds[1,0], bounds[0,1]],bounds[1],[bounds[0,0], bounds[1,1]] ])
            plt.plot(xy[:,0], xy[:,1])

            plt.triplot(self.x, self.y, self.tri[N['test_current_cells'],:])

            plt.title(f'Level {N["level"]} split dim  {int(N["level"]/2)}, Leaf cell {N["cellIDs"]}',)
            plt.show(block=True)

            import random
            mylist = ["left", "right"]

            #N  = N['left']
            #N = N['right']
            N = N[random.choice(mylist)]





if __name__ =='__main__':
    from oceantracker.util.ncdf_util import NetCDFhandler
    fn=r'C:\Work\oceantracker\tutorials_how_to\demo_hindcast\schsim3D\demo_hindcast_schisim3D_00.nc'
    nc = NetCDFhandler(fn)
    print(fn)
    d = nc.read_variables(['SCHISM_hgrid_node_x','SCHISM_hgrid_node_y','SCHISM_hgrid_face_nodes'])

    x,y, tri = d['SCHISM_hgrid_node_x'], d['SCHISM_hgrid_node_y'], d['SCHISM_hgrid_face_nodes'][:,:3]-1

    F= KDTreeCellFind(x,y,tri)
    F._plot_tree(25)
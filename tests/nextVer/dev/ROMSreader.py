from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from matplotlib import pyplot as plt, tri
from numba import njit

class ROMSreader(object):

    def __init__(self, fn):

        self.file_name=fn
        self.nc =NetCDFhandler(self.file_name)
        # subset fro testing,  384.2305  539.9580  896.4186  995.9659
        self.sel_lat=[384,539]
        self.sel_lon = [896, 995]

        self.grid = self._build_grid()

    def read_ROMS_grid(self):
        nc = self.nc
        grid={}
        grid['psi_mask'] = nc.read_a_variable('mask_psi').astype(np.int8)
        grid['lat'] = nc.read_a_variable('lat_psi')
        grid['lon'] = nc.read_a_variable('lon_psi')

        # tag open bounday  open and land mask

        return grid

    def read_water_velocity(self):
        # read water veocity anf move to psi grid
        nc = self.nc
        wv =[]
        u = nc.read_a_variable('u')
        u = (u[:,1:, :] + u[:,:-1, :])/2.0

        return wv

    def _build_grid(self):

        roms = self.read_ROMS_grid()
        # subset for testing
        for key in roms:
            roms[key] = roms[key][self.sel_lon[0]:self.sel_lon[1],self.sel_lat[0]:self.sel_lat[1]]

        # make tiangualtioon
        grid={'x': np.hstack((roms['lon'].flatten().reshape(-1,1),
                              roms['lat'].flatten().reshape(-1,1)))}

        # From PSI pmask make grid
        # in ROMS 1= ocean, 0=  2=?
        ocean_nodes= (roms['psi_mask']== 1).astype(np.int8)
        N, M = ocean_nodes.shape
        # find nodes having at least 1 ocean node left/right/above/below

        # pack to allow checking surounding points
        temp = np.full((N+2, M+2),-2)
        temp[1:-1,1:-1] = ocean_nodes
        sel = np.logical_or(temp[:-2 , 1:-1] == 1, temp[2: ,1:-1] == 1)
        sel = np.logical_or(sel, temp[1:-1, 2: ] == 1)
        sel = np.logical_or(sel, temp[1:-1, :-2] == 1)
        grid['nodes_to_keep'] = sel == 1  # psi nodes to keep  as 2D grid

        # get nindex of nodes to keep
        grid['x'] = grid['x'][np.flatnonzero(sel.flatten()),:]
        DT = tri.Triangulation(grid['x'][:, 0], grid['x'][:, 1])
        grid['triangles'] = DT.triangles


        # find node types, add possible open boundary first
        grid['node_type']= np.full_like(grid['nodes_to_keep'], 0,dtype=np.int8)
        grid['node_type'][[0,-1],:] =   2
        grid['node_type'][:, [0,-1]] =  2
        grid['node_type'][ocean_nodes == 0] = 1 # land=1, not ocean is 0

        grid['node_type']= grid['node_type'][grid['nodes_to_keep']].flatten()

        # remove triangles with 3 land nodes
        good = ~np.all(grid['node_type'][grid['triangles']] == 1, axis=1)
        grid['triangles'] = grid['triangles'][good,:]
        return grid

    def close(self):
        self.nc.close()

if __name__ == "__main__":

    fn= 'F:\\Hindcasts\\ROMtestdata\\Nordic-4km_SLEVELS_avg_00_subset2Feb2016.nc'
    fn= 'F:\\Hindcasts\Hindcast_samples_tests\ROMS_samples\ocean_his_0001.nc'
    R= ROMSreader(fn)
    R.read_water_velocity()

    if 1 == 1:
        plt.triplot(R.grid['x'][:, 0], R.grid['x'][:, 1], R.grid['triangles'], lw =0.3)

        sel= R.grid['node_type'] == 1
        plt.scatter(R.grid['x'][sel, 0], R.grid['x'][sel, 1],color='r',s=1)

        sel= R.grid['node_type'] == 2
        plt.scatter(R.grid['x'][sel, 0], R.grid['x'][sel, 1],color='g',s=1)
        plt.show()

    a=1

    R.close()

from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from matplotlib import pyplot as plt, tri
from numba import njit

class ROMSreader(object):

    def __init__(self, fn):

        self.file_name=fn
        self.nc =NetCDFhandler(self.file_name)
        self.grid = self.setup_grid()

    def read_ROMS_grid(self):
        nc = self.nc
        grid={}
        grid['psi_mask'] = nc.read_a_variable('mask_psi').astype(np.int8)
        grid['lat'] = nc.read_a_variable('lat_psi')
        grid['lon'] = nc.read_a_variable('lon_psi')

        # tag open boundary  open and land mask

        return grid

    def read_water_velocity(self, nb):
        # read water velocity anf move to psi grid
        nc = self.nc
        grid= self.grid
        nt = nc.get_dim_size('ocean_time')
        nz = nc.get_dim_size('s_rho')
        s1= (nt,nz, self.grid['nodes_to_keep'].size)
        s2 = (nt, + grid['x'].shape[0], nz ,3)
        nkeep = self.grid['nodes_to_keep'].flatten()

        uv = np.full(s2,np.nan, dtype= np.float32)

        u = nc.read_a_variable('u')
        u = (u[:,:, 1:, :] + u[:,:, :-1, :]) / 2.0
        uv[:, :, :, 0]  = u.reshape(s1)[:,:,nkeep].transpose((0,2,1))


        u = nc.read_a_variable('v').transpose((0,2,3,1))
        u = (u[:, :,:  1:] + u[:, :, :-1])/2.0
        uv[:, :, :, 1] = u.reshape(s1)[:, :, nkeep].transpose((0, 2, 1))
        # to add vertical vel if present

        return uv

    def setup_grid(self):

        roms = self.read_ROMS_grid()

        # make triangualtioon
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

    fn= 'F:\Hindcasts\Hindcast_samples_tests\ROMS_samples\ocean_his_0001.nc'
    #fn = 'F:\Hindcasts\Hindcast_samples_tests\ROMS_samples\\Nordic_subset_day1.nc' has zero pho cords

    R= ROMSreader(fn)
    nb= np.arange(10)
    R.read_water_velocity(nb)

    if 1 == 1:

        plt.triplot(R.grid['x'][:, 0], R.grid['x'][:, 1], R.grid['triangles'], lw =0.3)

        sel= R.grid['node_type'] == 1
        plt.scatter(R.grid['x'][sel, 0], R.grid['x'][sel, 1],color='r',s=1)

        sel= R.grid['node_type'] == 2
        plt.scatter(R.grid['x'][sel, 0], R.grid['x'][sel, 1],color='g',s=1)
        plt.show()

    a=1

    # build small version 25 by 25
    

    R.close()

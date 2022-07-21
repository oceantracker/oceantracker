from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from matplotlib import pyplot as plt, tri
from numba import njit

class ROMSreader(object):

    def __init__(self, fn):
        self.grid={}
        self.ROMSgrid = {}
        self.file_name=fn

        # subset fro testing,  384.2305  539.9580  896.4186  995.9659

        self.sel_lat=[384,539]
        self.sel_lon = [896, 995]

    def read_ROMS_grid(self):
        nc = NetCDFhandler(self.file_name)
        grid={}
        grid['mask'] = nc.read_a_variable('mask_psi')
        grid['lat'] = nc.read_a_variable('lat_psi')
        grid['lon'] = nc.read_a_variable('lon_psi')


        nc.close()
        return grid

    def _build_grid(self):

        roms = self.read_ROMS_grid()
        # subset fot tesing
        for key in roms:
            roms[key] = roms[key][self.sel_lon[0]:self.sel_lon[1],self.sel_lat[0]:self.sel_lat[1]]
        # make tiangualtioon
        grid= self._make_trianglation(roms)
        return grid


    def _make_trianglation(self, roms):
        grid={'x': np.hstack((roms['lon'].flatten().reshape(-1,1),roms['lat'].flatten().reshape(-1,1)))}

        DT =tri.Triangulation(grid['x'][:, 0],grid['x'][:, 1])

        grid['triangles'] = DT.triangles
        grid['triangles'] = mask_trianglation(roms['mask'].flatten(),grid['triangles'] )
        a=1

        if 1==1:
            plt.triplot(grid['x'][:, 0],grid['x'][:, 1],grid['triangles'] )
            plt.show()
        return grid

def mask_trianglation(mask, tri):
    masked_tri = np.full_like(tri,False)
    for ntri in np.arange(tri.shape[0]):
        for m in np.arange(3):
            masked_tri[ntri,m] = mask[tri[ntri,m]] == 1

    sel = np.all(masked_tri, axis=1)
    new_tri = tri[sel, :]
    return new_tri

if __name__ == "__main__":

    fn= 'F:\\Hindcasts\\ROMtestdata\\Nordic-4km_SLEVELS_avg_00_subset2Feb2016.nc'
    fn= 'F:\\Hindcasts\Hindcast_samples_tests\ROMS_samples\ocean_his_0001.nc'
    R= ROMSreader(fn)
    d = R._build_grid()
    a=1


import numpy as np

from oceantracker.util.ncdf_util import NetCDFhandler
from matplotlib import  pyplot as plt
from numba import njit
from oceantracker.reader.util.reader_util import get_values_at_ragged_bottom


fn =r'C:\data\NZ\NZfinite20170101_01z.nc'
fn=r'C:\data\sounds\schism_marl20170101_00z_3D.nc'
fn=r'C:\data\portGore\schout_Dec1.nc'
fn = r'D:\Hindcast_parts\blueEndeavourHindcastForRV\non-decay_20180901.nc'


nc = NetCDFhandler(fn)
d = nc.read_variables(['zcor','SCHISM_hgrid_node_x','SCHISM_hgrid_node_y','node_bottom_index','depth','SCHISM_hgrid_face_nodes'])

tri = d['SCHISM_hgrid_face_nodes'] - 1
zcor_depth= -get_values_at_ragged_bottom(d['zcor'][:,:,:,np.newaxis],d['node_bottom_index']-1)
nt = 0
zcor_depth=zcor_depth[nt,:,0]

depth = d['depth']
plt.scatter(depth,zcor_depth,s=4)
dmax = depth.max()
plt.plot([0,dmax],[0,dmax],c='g', lw=.1)
plt.plot([0,0],[0,dmax],c='g', lw=.1)
plt.plot([0,dmax],[0,0],c='g', lw=.1)
plt.xlabel('water_depth')
plt.ylabel('zcor water depth')

plt.title(fn)
plt.show()

plt.scatter(depth,zcor_depth-depth,s=4)
plt.xlabel('water_depth')
plt.ylabel('zcor water depth- water depth')

plt.title(fn)
plt.show()
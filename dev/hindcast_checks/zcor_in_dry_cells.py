import numpy as np

from oceantracker.util.ncdf_util import NetCDFhandler
from matplotlib import  pyplot as plt
from numba import njit
from oceantracker.reader.util.reader_util import get_values_at_ragged_bottom
from numba import njit

fn =r'C:\data\NZ\NZfinite20170101_01z.nc'

fn=r'C:\data\portGore\schout_Dec1.nc'
fn = r'D:\Hindcast_parts\blueEndeavourHindcastForRV\non-decay_20180901.nc'
fn=r'C:\data\sounds\schism_marl20170101_00z_3D.nc'
fn =r'D:\Hindcasts\UpperSouthIsland\2018_benHABS\nogrowth\1_Apr2018\Nydia_1.nc'

nc = NetCDFhandler(fn)
d = nc.read_variables(['zcor','SCHISM_hgrid_node_x','SCHISM_hgrid_node_y','node_bottom_index','depth','SCHISM_hgrid_face_nodes','wetdry_elem'])
x, y = d['SCHISM_hgrid_node_x'], d['SCHISM_hgrid_node_y']
tri = d['SCHISM_hgrid_face_nodes'] - 1
node_bottom_index = d['node_bottom_index'] -1
nt = 1
dry_tri = d['wetdry_elem'][nt]==1.
dry_nodes = tri[dry_tri,:3]

example_tri = dry_nodes[10,:]

zcor=d['zcor'][nt,example_tri,:]


# look at all nodes attached to dry triangles
s = 0
for n in np.unique(dry_nodes): #range(x.size):#
    t = tri[n,:4]
    z = d['zcor'][nt,n ,node_bottom_index[n]:]
    if np.all(z ==0):
        #print(n,z)
        s += 1

print(s,x.size)

plt.scatter(x[dry_nodes],y[dry_nodes], s=4)

plt.show()

pass
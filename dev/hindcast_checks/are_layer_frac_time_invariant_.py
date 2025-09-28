import numpy as np

from oceantracker.util.ncdf_util import NetCDFhandler
from matplotlib import  pyplot as plt
from numba import njit
from oceantracker.reader.util.reader_util import get_values_at_ragged_bottom
import numpy as np

fn =r'Z:\Hindcasts\NZ_region\2024_OceanNumNZ-2022-06-20\final_version\2017\01\NZfinite20170101_01z.nc'
#fn=r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD\2008\schism_marl20080101_00z_3D.nc'



nc = NetCDFhandler(fn)
d = nc.read_variables(['zcor','SCHISM_hgrid_node_x','SCHISM_hgrid_node_y','node_bottom_index','depth','SCHISM_hgrid_face_nodes'])

tri = d['SCHISM_hgrid_face_nodes'] - 1
nbot= d['node_bottom_index']-1

zcor_depth= get_values_at_ragged_bottom(d['zcor'][:,:,:,np.newaxis],nbot)[:,:,0]


frac = (d['zcor'] - zcor_depth[:,:, np.newaxis]) /(d['zcor'][:,:,-1]-zcor_depth)[:,:,np.newaxis]
nt=10
for n, nb in enumerate( np.unique(nbot)):
    sel = np.flatnonzero(nbot ==nb)
    ff = frac[nt,sel,nb:].T
    print('spatial range', nb,ff.max(axis=1)-ff.min(axis=1),)

for n, nb in enumerate( np.unique(nbot)):
    sel = np.flatnonzero(nbot ==nb)
    ff = frac[:,sel,nb:]
    range =  ff.max(axis=1)-ff.min(axis=1)
    print('time variation', nb,range.max(axis=1),)


if False:

    plt.scatter(frac,zcor_depth-depth,s=4)
    plt.xlabel('water_depth')
    plt.ylabel('zcor water depth- water depth')

    plt.title(fn)
    plt.show()
# rough code to conver a particluar matlab hind cast to schism
from os import path
from glob import glob
from oceantracker.util.ncdf_util import NetCDFhandler
import scipy.io
import numpy as np

input_dir= r'F:\Hindcasts\PortPhillipBay\HUY2020\matlab'
output_dir= r'F:\Hindcasts\PortPhillipBay\HUY2020\schism'

dims= ['nSCHISM_hgrid_node','two',]

for name in glob(path.join(input_dir, '*.mat')):
    print(name)
    f = scipy.io.loadmat(name)

    nc= NetCDFhandler(path.join(output_dir, path.basename(name).split('.')[0] + '.nc'),mode= 'w')


    a=['minimum_depth',
              'SCHISM_hgrid_node_x',
              'SCHISM_hgrid_node_y',
              'depth',
              'SCHISM_hgrid_face_nodes',
              'SCHISM_hgrid_edge_nodes']

    nc.write_a_new_variable('depth', np.squeeze(f['depth']), [dims[0]])
    nc.write_a_new_variable('SCHISM_hgrid_node_x',np.squeeze(f['lon']),[dims[0]], attributes=dict(units='degrees, east'))
    nc.write_a_new_variable('SCHISM_hgrid_node_y',np.squeeze(f['lat']),[dims[0]], attributes=dict(units='degrees'))

    nc.write_a_new_variable('time', np.squeeze(f['lat']), [dims[0]], attributes=dict(units='degrees'))


    pass

    nc.close()


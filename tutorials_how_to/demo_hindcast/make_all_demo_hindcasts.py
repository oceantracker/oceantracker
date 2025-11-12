import numpy as np
from glob import glob
from oceantracker.reader._oceantracker_dataset import OceanTrackerDataSet
from os import path

def compute_scale_and_offset_int16(data, missing_value=None):
    # scale data into int32's
    # mask and get min
    if missing_value is not None:
        data[data == missing_value] = np.nan
    dmin, dmax = np.nanmin(data), np.nanmax(data)

    # int 16 negative 32768 through positive 32767
    # stretch/compress data to the available packed range
    i16 =np.iinfo(np.int16)

    i16_range = float(i16.max - 1)  # range with last value reserved for missing value

    add_offset   = (dmin+.5*(dmax-dmin)).astype(data.dtype)
    scale_factor = ((dmax - add_offset)/i16_range).astype(data.dtype)

    # translate the range to be symmetric about zero


    # mask with new missing value
    missing_value = i16.max
    #data[np.isnan(data)] = missing_value
    #data = np.round(data,0).astype(np.int16)
    return scale_factor, add_offset, missing_value

def get_catalog(mask):
    params = dict(input_dir=path.dirname(mask), file_mask = path.basename(mask))
    return OceanTrackerDataSet(params)

def schism(m, args):
    # schism variants
    #todo hgrid file?
    i = dict(regular_grid=False)
    match m:
        case 0:
            i = dict(i, name='schsim3D',
                     is3D=True,
                     input_mask =r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD\2012\schism_marl201201*.nc',
                     ax = [],
                     vars=['SCHISM_hgrid_node_x','SCHISM_hgrid_node_y'],
                     node_dim='',
                     vert_dim='')
        case 1:
            i = dict(i, name='schsim2D',
                     is3D=False,
                     vars=[],vert_dim=''
                     )
        case 2:
            i = dict(i, name='schsim3Dv5',
                     vars=[])
    return i


def get_info(n, m, args):

    i = dict(scalar2D=[],scalar3D=[])

    match n:
        case 0:
            return schism(m, args)



if __name__ == '__main__':

    i= get_info(0, 0, None)
    # get list of
    catalog= get_catalog(i['input_mask'])
    pass
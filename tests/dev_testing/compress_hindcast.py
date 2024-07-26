import xarray as xr
from netCDF4 import Dataset
from os import path, mkdir
from glob import glob
import numpy as np
from copy import  deepcopy


def compute_scale_and_offset(data, n=16):
    min, max = data.min(), data.max()
    min,  max = float(min), float(max)
    # stretch/compress data to the available packed range
    scale_factor = (max - min) / (2 ** n - 1)
    # translate the range to be symmetric about zero
    add_offset = min + 2 ** (n - 1) * scale_factor
    return scale_factor, add_offset

def get_scale_offset(data):
    range = [data.min(), data.max()]
    pass
def compress(data):

    if data.nbytes < 10**6: return data

    encoding = deepcopy(data.encoding)
    #comp = dict(zlib=True, complevel=5)
    #encoding.update(zlib=True, complevel=5)
    #encoding['zlib']=True
    #encoding['complevel'] = 5


    match data.dtype:
         case np.float32:
             # scale_factor add_offset


            scale_factor, add_offset = compute_scale_and_offset(data)

            if 'missing_value' in encoding:
                 data = data.where(data != encoding['missing_value'], other=np.nan)

            data = (data - add_offset) / scale_factor
            if 'missing_value' in encoding:
                data = data.where(data != np.nan, other=np.iinfo(np.int16).min)

            data = data.astype(np.int16)
            data.attrs.update(scale_factor=scale_factor, add_offset=add_offset)

            data.encoding.update(encoding, dtype=np.int16, missing_value=np.iinfo(np.int16).min)

    return data



if __name__ == "__main__":
    output_dir = r'F:\temp\compress_test'
    input_dir =r'G:\Hindcasts_large\2024_OceanNumNZ-2022-06-20\final_version\2010\01'
    file_mask = 'NZfinite20100101_01z*.nc'
    input_dir= r'G:\Hindcasts_large\2024_hauraki_gulf_auck_uni\2019\01'
    file_mask = 'schout_1.nc'

    mask =  path.join(input_dir,'**',file_mask)

    files = glob(mask, recursive=True)

    if not path.isdir(output_dir):
        mkdir(output_dir)

    for file in files:

        file_name = path.basename(file)
        file_dir = path.dirname(file).replace(input_dir,'')
        file_out = path.join(output_dir,file_dir,'comp_'+ file_name )


        ds = xr.open_dataset(file, engine='netcdf4')

        for v in list(ds.variables):
            #print(v,np.any(np.isnan(ds[v])))
            ds[v] = compress(ds[v])
        pass

        comp = dict(zlib=True, complevel=5)
        encoding = {var: comp for var in ds.data_vars}
        ds.to_netcdf(file_out, encoding=encoding)

        # test
        ds1 = xr.open_dataset(file)
        ds2 = xr.open_dataset(file_out)
        nc2 = Dataset(file_out)

        for v in ds.data_vars:
            print(v, 'maxdiffs', float((ds1[v]-ds2[v]).max()))
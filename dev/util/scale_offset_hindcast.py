import xarray as xr
import numpy as np
from glob import  glob
from os import  path, mkdir
from datetime import datetime
#from oceantracker.util.xarrry_util import compute_scale_and_offset_int16
from demos.demo_hindcast.make_demo_schism_hindcast import compute_scale_and_offset_int16
import multiprocessing
from copy import  copy
def scale_file(args):
    d0= datetime.now()
    subset,n_proc, fn_in, fn_out, space_dim, n_files = args
    print(f'{subset::02d}:{n_proc::04d} starting -  {path.basename(fn_in)},{fn_out}')

    ds = xr.open_dataset(fn_in)
    encoding={}
    for name, v in ds.variables.items():
        # scale fields
        e={}
        if v.ndim > 1 and space_dim in v.dims and (v.dtype == np.float32 or v.dtype == np.float64):
            scale_factor, add_offset, missing_value = compute_scale_and_offset_int16(v, missing_value=None)
            e.update(dict(scale_factor=scale_factor, add_offset=add_offset, missing_value=missing_value,
                           dtype=np.int16, zlib=True, complevel=5
                           ))
        encoding[name] = e

    if not path.isdir(path.dirname(fn_out)):  mkdir(path.dirname(fn_out))
    print(f'\t {n_proc:04d} writing  {str(datetime.now() - d0)} -  {path.basename(fn_in)}')
    ds.to_netcdf(fn_out, encoding=encoding)
    print(f'\t {n_proc:04d} of {n_files} done - {path.basename(fn_in)}, {str(datetime.now() - d0)}')


if __name__ == "__main__":
    h = 0
    subsets=[0]
    match h:
       case 0:
            space_dim = 'nSCHISM_hgrid_node'
            din=r'Y:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD'
            dout = r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD'
            subsets=[f'{int(x)}'  for x in range(2010,2018)]

    if not path.isdir(dout):
        mkdir(dout)


    #file_list =[file_list[0]]
    d0= datetime.now()
    args=[]
    #file_list=file_list[:2]

    for s in subsets:
        d1 = f'{din}\{s}'
        file_list = glob(path.join(d1, '**', '*.nc'), recursive=True)
        d2 = f'{dout}\{s}'
        for n, f_in in enumerate(file_list):
            f_out = d2 + f_in.split(path.abspath(d1))[-1]
            args.append((s,n,copy(f_in),copy(f_out),space_dim))
    pass

    args = [a.append(len(file_list)) for a in args] # add total number of files tp args

    with multiprocessing.Pool(processes=10) as pool:
        case_summaries = pool.map(scale_file, args)

    dt= datetime.now() - d0
    print(f'total time {str(dt)}, sec per file= {dt.seconds/len(file_list)}')
    # check last file
    ds1= xr.open_dataset(args[0][1])
    ds2 = xr.open_dataset(args[0][2])

    for name, v in ds1.variables.items():
        d1 = v.compute().data
        d2 = ds2[name].compute().data
        d = d1- d2
        print(name,'min ', np.nanmin(d),' in ',np.nanmin(d1), 'max ', np.nanmax(d) ,' in ',np.nanmax(d1) )

from oceantracker.util.ncdf_util import NetCDFhandler
from os import  path
import xarray as xr
import numpy as np

defaut_particle_chunks =100_000
def convert_compact_file(compact_file_name, particle_chunks=defaut_particle_chunks):

    #f = NetCDFhandler(compact_file_name,mode='r')
    f1 = xr.open_dataset(compact_file_name,
                         decode_times=False,decode_coords=False,
                         decode_cf=False, use_cftime=False,  decode_timedelta=False)
    f2 = xr.Dataset()

    f2.attrs = f1.attrs

    # do  non-compact first to get time/part dim set up
    for name, val in f1.variables.items():
        if not 'time_particle_dim' in val.dims:
              f2[name] = val

    f2 = f2.chunk(dict(time_dim=24, particle_dim=particle_chunks))

    # convert compacted variables
    for name, val in f1.variables.items():
        if 'time_particle_dim' in val.dims:
            f2[name] = convert_var(name,f1,particle_chunks=particle_chunks)

    f2.to_netcdf(compact_file_name.replace('compact','rectangular'))
    pass

def convert_var(var_name,data_set,  particle_chunks=defaut_particle_chunks):
    var = data_set[var_name]

    time_dim,part_dim =data_set.time.dims[0],data_set.ID.dims[0]
    dims2 = [time_dim,part_dim] + list(var.dims[1:])
    shape2 = [data_set.sizes[dn] for dn in dims2]
    fill = np.nan if np.issubdtype(var.dtype,np.floating) else np.iinfo(var.dtype).min
    d2 = xr.DataArray(dims=dims2,data = np.full(shape2, fill, dtype=var.dtype),
        attrs=var.attrs)

    # insert data
    _unpack_compact_data(var.data, data_set['time_step_range'].data,
                        data_set.particle_ID.data, d2.data )
    return  d2

def _unpack_compact_data(data,time_step_range,ID, result):
    # insert data
    # time_step_range is the time steps in complete run, not just this file
    #s= (time_step_range.shape[0],int(ID[-1]-ID[0]+1),) + data.shape[1:]
    #result = np.full(())
    ID0= ID[0]
    for nt in range(time_step_range.shape[0]):
        r = range(0,time_step_range[nt,1]-time_step_range[nt,0])
        d = data[r,...]
        i = ID[r] - ID0
        for n in range(i.size):
            result[nt,i[n],...] = d[n,...]




if __name__ == "__main__":

    dir =r'C:\Auck_work\oceantracker_output\unit_tests\unit_test_08_statistics_00'
    fn =path.join(dir,'unit_test_08_statistics_00_tracks_compact_000.nc')
    convert_compact_file(fn, particle_chunks=100_000)
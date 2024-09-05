from oceantracker.util.ncdf_util import NetCDFhandler
from os import path
import numpy as np
from  matplotlib import  pyplot as plt
import glob
import xarray as xr
from copy import deepcopy
from make_demo_schism_hindcast import compute_scale_and_offset_int16

if __name__ == '__main__':

    data_file_mask =r'F:\Hindcast_parts\ROMS_Mid_Atlantic_Bight\doppio_his_20171101_0000_0001*.nc'
    #ax=    1.0e+06 *np.asarray([ 1.5903,    1.6026,    5.4795,    5.501]) # abel tasman
    out_file_base='demo_hindcast_roms'
    nz0=22
    nt_step=2
    n_files=1


    # find sub domain
    file_list=glob.glob(data_file_mask)
    for n_file, fn in enumerate(file_list[:n_files]):

        ds_in= xr.open_dataset(fn, chunks=dict(time=1))

        keep_vars=['h','w','temp','u','v','ubar','vbar', 'lat_psi','zeta',
                   'lat_rho', 'lat_u', 'lat_v', 'lon_psi', 'lon_rho', 'lon_u', 'lon_v',
                   'mask_psi', 'mask_rho', 'mask_u', 'mask_v',
                   's_rho','s_w','ocean_time']
        drop_vars=  set(ds_in.variables.keys()) .difference(keep_vars)
        ds_in = ds_in.drop_vars(drop_vars)

        # these start on rho points
        xi_rho = ds_in.dims['xi_rho']
        xi_psi = ds_in.dims['xi_psi']
        # were to take sub-grid,(43,-60)
        rows = 20
        cols=25
        c0 = 158
        r0 = 106-rows

        sel=dict()

        dims =ds_in.dims
        for name, d in dims.items():

            if 'eta_' in name:   # rows
                i0 = r0
                i1 = r0 +rows - ('_v' in name or 'psi' in name)
            elif 'xi_' in name: # cols
                i0 = c0
                i1 = c0 + cols - ('_u' in name or 'psi' in name)
            else: continue

            sel[name]= range(i0,i1 )

        sel['s_rho'] = range(0,dims['s_rho'],2) # works as original 40 is divisible by 2
        sel['s_w'] = range(0, dims['s_w'], 2)
        pass
        ds_out= ds_in.isel(sel).compute()

        e = {}
        for name, v in ds_out.variables.items():
            if any('eta_' in x for x in v.dims) or any('xi_' in x for x in v.dims):
                scale_factor, add_offset, missing_value = compute_scale_and_offset_int16(v, missing_value=None)
                e[name] = dict(scale_factor=scale_factor, add_offset=add_offset, missing_value=missing_value, dtype=np.int16,
                               zlib=True, complevel=9,
                               # _FillValue =missing_value
                               )
        out_file = path.join('ROMS', f'ROMS3D_{n_file:02d}.nc')
        ds_out.to_netcdf(out_file, encoding=e)
        pass

    # read and plot
    print('reading',out_file)
    r = NetCDFhandler(out_file)
    var = r.read_variables(r.all_var_names())
    x, y =var['lon_rho'],var['lat_rho']
    depth = var['h']
    depth[var['mask_rho']==0]=np.nan
    #plt.pcolor(x, y, depth)
    plt.scatter(x, y,s=5,marker='.',c='k')
    sel = var['mask_rho'] == 0
    plt.scatter(x[sel], y[sel], s=5, marker='.', c='b')

    x, y = var['lon_psi'], var['lat_psi']
    sel = var['mask_psi'] == 0
    plt.scatter(x[sel], y[sel],s=16,marker='x', c='r')
    plt.scatter(x[~sel], y[~sel], s=4, marker='x', c='k')

    x, y = var['lon_v'], var['lat_v']
    sel = var['mask_v'] == 0
    plt.scatter(x[sel], y[sel],marker='^', s=12, c='g')

    x, y = var['lon_u'], var['lat_u']
    sel = var['mask_u'] == 0
    plt.scatter(x[sel], y[sel],marker='>', s=12, c='y')

    #plt.pcolor(depth)
    plt.show()


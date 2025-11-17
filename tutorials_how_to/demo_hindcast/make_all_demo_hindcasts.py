import numpy as np
from glob import glob

from os import path, makedirs, remove
import argparse
import xarray as xr

from oceantracker.util import ncdf_util, time_util


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

def get_catalog(i, args):
    # for each variable get t a list of files with each variable

    file_list= glob(path.join(path.dirname(i['input_mask']),'**',  path.basename(i['input_mask'])),
                    recursive=True)
    file_list = np.asarray(file_list)
    vars={}
    f_start_retimes =[]
    for fileID,f in enumerate(file_list):

        # assumes time in every file
        #nc = NetCDFhandler(f)
        #nc.close()
        ds = xr.open_dataset(f, decode_times=False, decode_coords=False,decode_timedelta=False)
        t0 =float(ds[i['grid']['time']].compute().data[0])
        t1 = float(ds[i['grid']['time']].compute().data[0])

        for v,data in ds.variables.items():
            if v not in vars: vars[v] = dict(fileIDs=np.zeros((0,),dtype=np.int32), t0=np.zeros((0,),dtype=np.float64))
            d = vars[v]
            d['t0'] = np.append(d['t0'],t0)
            d['fileIDs'] = np.append(d['fileIDs'],fileID)


    # sort variable filesIDs into time order
    tmax = 15*24*3600 if args.full else 24*3600

    for name, d in vars.items():
        file_order = np.argsort(d['t0'])
        d['t0'] = d['t0'][file_order]
        d['fileIDs'] = d['fileIDs'][file_order]
        d['files'] =   [ file_list[ID] for ID in  d['fileIDs']]

        # only keep files up to tmax
        nts = np.flatnonzero(d['t0'] - d['t0'][0] < tmax)
        d['t0'] = d['t0'][nts]
        d['fileIDs'] = d['fileIDs'][nts]
        d['file_names'] = file_list[d['fileIDs'] ]

    # now build a  dict of unique files with the variables in each
    files=dict()
    for name, d in vars.items():
        for  f in d['file_names']:
            key = str(f)
            if f not in files: files[key]=[]
            files[key].append(name)
    required_files =[[name, vars]  for name, vars in files.items() ]
    return required_files


def get_triangulation(i, required_files) :
    # get triangulations and nodes inside axis_lims
    grid = i['grid']

    # find first file with node coords
    for name, v in required_files :
        ds = xr.open_dataset(name, decode_times=False, decode_coords=False,decode_timedelta=False)
        if grid['x_node'] in ds.variables: break

    x = ds[grid['x_node']].compute().data
    y = ds[grid['y_node']].compute().data
    tri = ds[grid['triangulation']].compute().data
    sel = np.isnan(tri)
    missing = -9990
    tri[sel] = missing
    tri = tri.astype(np.int32) - int(i['one_based']) # zero based indcies for python


    # find  triangles in sub-domain
    x_tri = np.mean(x[tri[:, :3]], axis=1)
    y_tri = np.mean(y[tri[:, :3]], axis=1)

    ax = i['axis_limits']
    sel_tri = np.logical_and.reduce((x_tri > ax[0], x_tri < ax[1], y_tri > ax[2], y_tri < ax[3]))
    sel_tri = np.flatnonzero(sel_tri)

    required_tri = tri[sel_tri, :]

    required_nodes=np.unique(required_tri[required_tri >=0])
    required_nodes = np.sort(required_nodes)

    new_triangulation = np.full((sel_tri.shape[0],4),missing,np.int32)
    for n, val in enumerate(required_nodes.tolist()):
        sel = int(val) == required_tri # where tri matches the required nodes
        new_triangulation[sel]= n +  int(i['one_based'])

    new_triangulation[new_triangulation < 0 ] = -1 # make missing 4th values the same

    if False:
        import matplotlib.pyplot as plt
        plt.scatter(x,y,s=.1)
        plt.scatter(ax[0], ax[2], c='r')
        plt.scatter(ax[1], ax[3], c='g')
        plt.show()


    return dict(required_tri=required_tri,required_nodes=required_nodes,
                new_triangulation=new_triangulation,
                triangulation_dims= ds[grid['triangulation']].dims)

def write_files(i, required_files, args):

    out_dir = r'F:\H_Local_drive\ParticleTracking\demo_hindcasts'
    out_dir = path.join(out_dir,f'{i["name"]}')
    if not path.exists(out_dir):
        makedirs(out_dir)
    else:
        # delete old files
        for f in glob(out_dir+'/*'):
            remove(f)

    # find file with coords and get new triangulation
    info = get_triangulation(i, required_files)

    required_files = [ [n,]+r for n, r in enumerate(required_files)]# add index to order info to required_files
    order = np.random.choice(len(required_files), len(required_files), replace=False)
    for nn, o in enumerate(order):
        ID, file, vars = required_files[o]
        ds = xr.open_dataset(file, decode_times=False, decode_coords=False,decode_timedelta=False)

        ds_out = xr.Dataset()

        # copy attributes
        for name, val in ds.attrs.items(): ds_out.attrs[name] = val

        dims = i['dims']

        copy_vars = i['required_vars']
        # add first optional if found
        for v in i['optional_vars']:
            if v in ds.variables:
                copy_vars.append(v)
                break

        encoding = {}
        grid = i['grid']
        # add triangulation
        if i['structured']:
            pass
        else:
            # unstructured
            ds_out[grid['triangulation']] = xr.DataArray(info['new_triangulation'], dims=info['triangulation_dims'])
            node_dim = dims['node']

            if grid['x_node'] in ds.variables:
                ds_out[grid['x_node']] = ds[grid['x_node']].compute().isel({node_dim: info['required_nodes']})
                ds_out[grid['y_node']] = ds[grid['y_node']].compute().isel({node_dim: info['required_nodes']})

            if grid['bottom_bin'] in ds.variables:
                ds_out[grid['bottom_bin'] ] = ds[grid['bottom_bin']].compute().isel({node_dim: info['required_nodes']}).astype(np.int32)

            # add time
            if  grid['time'] in ds.variables:  ds_out[grid['time'] ] = ds [grid['time'] ]

            for v in copy_vars:
                if v not in ds.variables: continue
                ds_out[v] = ds[v].compute().isel({node_dim: info['required_nodes']})

                # compress floats
                if np.issubdtype(ds_out[v],np.floating):
                    scale_factor, add_offset, missing_value = compute_scale_and_offset_int16( ds_out[v], missing_value=None)
                    encoding[v] = dict(scale_factor=scale_factor, add_offset=add_offset, missing_value=missing_value,
                                   dtype=np.int16,  zlib=True, complevel=9 )

        # decimate to hourly
        if dims['time'] in ds_out.dims:
            ds_out = ds_out.isel( {dims['time'] : slice(None, None, i['time_decimation'])})

        fn = path.join(out_dir,   f'{i["name"]}_{nn:03d}_time_order{ID:03d}.nc')
        print('writing file: ',path.basename(fn))

        ds_out.to_netcdf(fn, encoding=encoding)
        print('\t done file: ', fn)
        pass


def schism(m, args):
    # schism variants
    #todo hgrid file?

    schism3D = dict( name='schism3D', structured=False, is3D=True, regular_grid=False,one_based=True,
                    time_decimation=2,
                    axis_limits =  1.0e+06 *np.asarray([ 1.5903,    1.6026,    5.4795,    5.501]), # abel tasman
                    input_mask =r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD\2012\schism_marl201201*.nc',
                    grid = dict(triangulation='SCHISM_hgrid_face_nodes',
                                x_node='SCHISM_hgrid_node_x',
                                y_node='SCHISM_hgrid_node_y',
                                time='time',
                                bottom_bin = 'node_bottom_index'),
                    required_vars=['zcor','depth','elev','hvel', 'diffusivity','bottom_stress','vertical_velocity'],
                    optional_vars=['temp','sal'],
                    dims=dict(
                            time='time',
                            node='nSCHISM_hgrid_node')
                            )
    # set up variants
    match m:
        case 0:
            return schism3D
        case 1:
            schism3D.update( name='schism3D_v5', structured=False, is3D=True, regular_grid=False,one_based=True,
                    class_name='SCHISMreader',
                    time_decimation=2,
                    input_mask=r'F:\Hindcast_reader_tests\Schimsv5\HaurakiGulfv5\01\*.nc',
                    axis_limits=[174.74131848445504, 174.92349387270926,-36.69635808784122,  -36.58458475941872],
                   required_vars = ['horizontalVelX', 'horizontalVelY', 'verticalVelocity',
                                                          'diffusivity', 'bottomStressX', 'bottomStressY']
                )

            return schism3D
            pass



def get_info(n, m, args):

    match n:
        case 0:
            return schism(m, args)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple script to greet a user.")
    parser.add_argument('-full',   action="store_true",  help="long demo hindcasts"    )
    args = parser.parse_args()

    m= 1

    i= get_info(0, m, args)
    # get list of
    required_files= get_catalog(i,args)
    write_files(i, required_files, args)

    pass
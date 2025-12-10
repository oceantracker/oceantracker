import numpy as np
from glob import glob
from copy import deepcopy
from os import path, makedirs, remove
import argparse
import xarray as xr
from oceantracker.util import class_importer_util, parameter_checking, message_logger, json_util, time_util
missing_int = -9999

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
    # translate the range to be symmetric about zero
    add_offset   = (dmin+.5*(dmax-dmin)).astype(data.dtype)
    scale_factor = ((dmax - add_offset)/i16_range).astype(data.dtype)

    # mask with new missing value
    missing_value = i16.max
    #data[np.isnan(data)] = missing_value
    #data = np.round(data,0).astype(np.int16)
    return scale_factor, add_offset, missing_value

def get_required_var_names(i,args):
    # build variable lists from  reader
    msg_logger=message_logger.MessageLogger()
    ci= class_importer_util.ClassImporter(msg_logger)
    m = i['class_name'][:i['class_name'].rfind('.')]
    mod= ci._import_module_from_string(m)
    c = i['class_name'][i['class_name'].rfind('.')+1:]
    reader = getattr(mod,c)()

    params = dict(class_name=i['class_name'], input_dir= i['input_dir'], file_mask= i['file_mask'])

    params = parameter_checking.merge_params_with_defaults(params,reader.default_params, msg_logger)
    fmap =  params['field_variable_map']

    def add_var(ty, i, map, v):
        if ty not in i: i[ty] =[]
        if v not in map: return
        if type(map[v]) == list:
            i[ty] += map[v]
        else:
            i[ty].append(map[v])

    # get required vars for mapped variables, if in file
    for v in   ['water_velocity','tide','bottom_stress',  'water_velocity_depth_averaged', 'wind_stress',
                'water_depth','A_Z_profile']:
        add_var('required_vars',i, fmap, v)

    # add possible optional scalar vars
    for v in   ['water_temperature','salinity']:  add_var('optional_vars',i, fmap, v)

    # required grid variables
    for v in ['x','y','z_interface','bottom_interface_index','is_dry_cell']:  add_var('required_vars',i, params['grid_variable_map'], v)


    # add required dimensions
    dm = params['dimension_map']
    if 'dims' not in i : i['dims'] = {}
    for v in ['node','cell','row','col']:
        if v in dm: i['dims'][v] = dm[v]

      # add grid variables
    # add dimensions
    i['grid']= g = {}
    gmap = params['grid_variable_map']
    g['x_node'],g['y_node'] = gmap['x'], gmap['y']

    if i['structured']:
        pass
    else:
        g['triangulation'] = gmap['triangles']
    i['time_var'] = gmap['time']

    i['required_vars'] = list(set(i['required_vars'])) # make list unique

    if args.full: i['name'] += f'_{i["label"]}'  # tag full dir with label
    i['reader'] = reader
    return i

def _ensure_int(data):
    if np.issubdtype(data.dtype, np.floating):
        sel = np.isnan(data)
        data[sel] = missing_int
        data = data.astype(np.int32)  # zero based indcies for python
    return data

def get_triangulation(i,file_list) :
    # get triangulations and nodes inside axis_lims
    grid = i['grid']

    # find first file with node coords
    for name in file_list :
        ds = xr.open_dataset(name, decode_times=False, decode_coords=False,decode_timedelta=False)
        if grid['x_node'] in ds.variables: break
        ds.close()

    x = ds[grid['x_node']].compute().data
    y = ds[grid['y_node']].compute().data
    tri = _ensure_int(ds[grid['triangulation']].compute().data) - int(i['one_based'])

    # find  triangles in sub-domain
    x_tri = np.mean(x[tri[:, :3]], axis=1)
    y_tri = np.mean(y[tri[:, :3]], axis=1)

    if False:
        import matplotlib.pyplot as plt
        plt.triplot(x, y, tri[:,:3], c=[.8,.8,.8], lw=.5)
        if  'axis_limits' in i:
            ax = i['axis_limits']
            plt.scatter(ax[0], ax[2], c='r')
            plt.scatter(ax[1], ax[3], c='g')
        if 'coast_point' in i:
            plt.scatter(i['coast_point'][0], i['coast_point'][1], marker='x', c='g')
        if 'deep_point' in i:
            plt.scatter(i['deep_point'][0], i['deep_point'][1],marker='x', c='g')
        xy= plt.ginput(2)
        print([float(v) for v in np.asarray(xy).ravel()])
        plt.show()


    ax = i['axis_limits']
    sel_tri = np.logical_and.reduce((x_tri > ax[0], x_tri < ax[1], y_tri > ax[2], y_tri < ax[3]))
    sel_tri = np.flatnonzero(sel_tri)

    required_tri = tri[sel_tri, :]

    required_nodes=np.unique(required_tri[required_tri >=0])
    required_nodes = np.sort(required_nodes)

    new_triangulation = np.full((sel_tri.shape[0],tri.shape[1]),missing_int,np.int32)
    for n, val in enumerate(required_nodes.tolist()):
        sel = int(val) == required_tri # where tri matches the required nodes
        new_triangulation[sel]= n +  int(i['one_based'])

    new_triangulation[new_triangulation < 0 ] = -1 # make missing 4th values the same

    return dict(required_cells=sel_tri,required_nodes=required_nodes,
                new_triangulation=new_triangulation,
                triangulation_dims= ds[grid['triangulation']].dims)

def write_files(i, args):

    file_list = glob(path.join(i['input_dir'], '**', i['file_mask']), recursive=True)

    out_dir = path.join(i['output_dir'],f'{i["name"]}')

    if not path.exists(out_dir):
        makedirs(out_dir)
    else:
        # delete old files
        for f in glob(out_dir+'/*'):
            remove(f)

    if 'dim_slices' not in i: i['dim_slices'] = {}
    dims = i['dims']

    # scan files for first time_dim etc
    t0= float(np.inf)
    for n, name in enumerate(file_list):
        ds = xr.open_dataset(name, decode_times=False, decode_coords=False,
                             decode_timedelta=False,mask_and_scale=False)

        if i['time_var'] in ds.variables:
            dims['time'] = ds[ i['time_var']].dims[0]
            t0_file =  i['reader'].decode_time(ds[i['time_var']][0]) # decode with reader to ensure its in seconds since 1970
            t0  = min( float(t0_file), t0)
        ds.close()


    # find file with coords and get new triangulation
    if not i['structured']:
        # set up slices for unstructured grid
        info = get_triangulation(i, file_list)
        i['dim_slices'][dims['node']] = info['required_nodes']
        i['dim_slices'][dims['cell']] = info['required_cells']
        print('compressed: unstructured grid  nodes = ', info['required_nodes'].size, 'cells', info['required_cells'].size,)


    tmax = 14*24*3600 if args.full else 24*3600

    for nn, file in enumerate(file_list):

        ds = xr.open_dataset(file, decode_times=False, decode_coords=False,decode_timedelta=False)
        if i['time_var'] in ds.variables:
            # only copy files with first tmax of first time
            file_times = i['reader'].decode_time(ds[i['time_var']]) # decode with reader to ensure its in seconds since 1970
            if  file_times[0]-t0 >= tmax: continue
            print(f'\t\t times  {time_util.seconds_to_isostr(file_times[0])} to {time_util.seconds_to_isostr(file_times[-1])}, timesteps= {file_times.size}')
            #  time decimate whole dataset, won't work on one time step per file
            if dims['time'] in ds.dims:
                ds = ds.isel({dims['time']: slice(None, None, i['time_decimation'])})

        print('starting file: ', file)
        print('\t\t vars', list(ds.variables.keys()))
        print('\t\t\t dims', dict(ds.dims))


        ds_out = xr.Dataset()

        # copy attributes
        #for name, val in ds.attrs.items(): ds_out.attrs[name] = val

        dims = i['dims']

        copy_vars = i['required_vars']
        # add first optional  variable if found
        for v in i['optional_vars']:
            if v in ds.variables:
                copy_vars.append(v)
                break

        encoding = {}
        grid = i['grid']
        # add triangulation if present
        if 'triangulation' in grid and grid['triangulation'] in ds.variables:
            ds_out[grid['triangulation']] = xr.DataArray(info['new_triangulation'], dims=info['triangulation_dims'])


        # loop over vars
        for v in copy_vars:
            if v not in ds.variables: continue
            print('\t\t compressing var=', v, '\t\t Dims', dict( ds[v].sizes))
            data= ds[v].compute()
            # loop over all slicing
            for dim,s  in i['dim_slices'].items():
                if dim  in data.dims:
                    data= data.isel({dim:s})

            # compress time varying floats
            if dims['time'] in  data.dims and np.issubdtype(data,np.floating):
                scale_factor, add_offset, missing_value = compute_scale_and_offset_int16(data, missing_value=None)
                encoding[v] = dict(scale_factor=scale_factor, add_offset=add_offset, missing_value=missing_value,
                               dtype=np.int16,  zlib=True, complevel=9 )
            ds_out[v] = data.compute()

        fn = path.join(out_dir,   f'{i["name"]}_{nn:03d}.nc')

        if len(ds_out.variables) > 0:
            print('\t writing file: ', path.basename(fn), 'variables', list(ds_out.variables.keys()))
            ds_out.to_netcdf(fn, encoding=encoding)
            print('\t\t done file: ', fn)
            print('\t\t dims', dict(ds_out.sizes))
        ds_out.close()

    # write release point json
    p = dict()
    if 'coast_point' in i: p['coast_point']=i['coast_point']
    if 'deep_point' in i: p['deep_point'] = i['deep_point']

    json_util.write_JSON(path.join(out_dir, 'info.json'), p)


def run(i,output_dir, args):

    file_base = i['name']
    input_dir = path.join(i['output_dir'],file_base)

    from oceantracker.main import OceanTracker
    ot = OceanTracker()
    ot.settings(root_output_dir=output_dir, output_file_base=file_base, time_step=10*60, debug=True)
    ot.add_class('reader', input_dir=input_dir, file_mask=file_base + '*.nc')

    info = json_util.read_JSON(path.join(input_dir, 'info.json'))

    pulse_size= 100 if args.full else 10
    release_interval = 3600

    if 'deep_point' in info:
        ot.add_class('release_groups', points=info['deep_point'],
                     release_interval=release_interval, pulse_size=pulse_size, name='deep_point', )
    if 'coast_point' in info:
        ot.add_class('release_groups', points=info['coast_point'],
                     release_interval=release_interval, pulse_size=pulse_size, name='coast_point' )
    case_info_file_name= ot.run()
    return case_info_file_name


def schism(args):
    # schism variants
    #todo hgrid file?
    base = dict(structured=False, one_based=True,)
    schism3D = deepcopy(base)
    schism3D.update( name='schism3D',  time_decimation=2,is3D=True,label='MalbroughSounds_10year',
                    axis_limits =  1.0e+06 *np.asarray([ 1.5903,    1.6026,    5.4795,    5.501]), # abel tasman
                    input_dir =r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD\2012',
                    file_mask= r'schism_marl201201*.nc',
                    class_name= 'oceantracker.reader.SCHISM_reader.SCHISMreader',
                    deep_point=[1594000, 5484200, -2],
                          )

    schism2D = deepcopy(base)
    schism2D.update( name='schism2D',  time_decimation=1, is3D=False,label='Port_Philip_bay',
                    axis_limits = [143.92515111738638, 144.20689192125877,-38.5723758591546,  -38.44437128551422], # abel tasman
                    #input_dir =r'D:\Hindcast_reader_tests\Schisim\PPB_Hydro_netCDF',
                     input_dir= r'D:\Hindcasts\Australia\2022_PortPhillipBay2020\HUY2020\schism',
                    file_mask= r'202001*.nc',
                    class_name= 'oceantracker.reader.SCHISM_reader.SCHISMreader',
                    deep_point=[144.0824017986175, -38.523889278230214, -2],
                          )

    schism3Dv5 = deepcopy(base)
    dx = 0.05
    schism3Dv5.update(name='schism3D_v5', is3D=True,label='HaurakiGulfv5',
           class_name='oceantracker.reader.SCHISM_reader_v5.SCHISMreaderV5',
           time_decimation=1,
           input_dir=r'F:\Hindcast_reader_tests\Schimsv5\HaurakiGulfv5\01',
            file_mask = r'*.nc',
            axis_limits=[175-dx,175.18+dx,-36.4-dx,-36.125+dx],
            deep_point=[175.1, -36.3, -2],
            coast_point=[175.05, -36.225] )

    return [schism3D, schism3Dv5, schism2D]

def GLORYS(args):

    base = dict(structured=True, one_based=True,
                class_name= 'oceantracker.reader.GLORYS_reader.GLORYSreader',)
    GLORYS3DfizedZ = deepcopy(base)
    GLORYS3DfizedZ.update( name='Glorys3DfixedZ',  time_decimation=1,
                           is3D=True,label='BalticSea',
                           #label='NZregion',

                    #input_dir =r'D:\Hindcast_reader_tests\Glorys\glorys_seasuprge3D',
                    #file_mask='cmems*.nc',
                    input_dir=f'D:\Hindcast_reader_tests\Glorys\BalticSea',
                    file_mask='BAL**.nc',
                    # slice regular grids
                    dim_slices = dict(lat=range(400,450),
                                      lon=range(400,450),
                                    latitude=range(400, 450),
                                    longitude=range(400, 450)),
                    required_vars=['mask'],
                    deep_point=[20.5,59.9,  -2],
                    #coast_point=[175.05, -36.225],
                     )
    return [GLORYS3DfizedZ]

def ROMS(args):

    base = dict(structured=True, one_based=True,
                class_name= 'oceantracker.reader.ROMS_reader.ROMSreader',)
    ROMS1 = deepcopy(base)
    r,c, e = 50, 190, 50
    ROMS1.update( name='ROMS3Dsigma',  time_decimation=1,
                           is3D=True,label='MidAtlanticBight',
                           #label='NZregion',

                    input_dir=r'D:\Hindcast_reader_tests\ROMS_samples\ROMS_Mid_Atlantic_Bight',
                    file_mask= 'doppio_his_2017*.nc',
                    # slice regular grids, but rms has several grids!
                    dim_slices = dict(eta_psi=range(r,r+e),
                                        xi_psi=range(c,c+e),
                                        eta_u=range(r, r + e+ 1),
                                         xi_u=range(c, c + e ),
                                        eta_v=range(r, r+e),
                                        xi_v=range(c, c+e+1),
                                        xi_rho=range(c, c+e+1),
                                      eta_rho=range(r, r + e + 1),
                                      ),
                    required_vars=['mask_psi','mask_u','mask_v','mask_rho'],
                    #deep_point=[-66,  43],
                  deep_point=[-66.00172985389652,   44.91244933089063]
                    #coast_point=[175.05, -36.225],
                     )
    return [ROMS1]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple script to greet a user.")
    parser.add_argument('-full',   action="store_true",  help="long demo hindcasts"    )
    parser.add_argument('-type', type=int, default=-1)
    parser.add_argument('-variant', type=int, default=-1)
    parser.add_argument('-run_off', action="store_true", help=" toggle run demo hindcasts off ")
    parser.add_argument('-write_off', action="store_true", help="toggle write hindcast off")
    parser.add_argument('-plot', action="store_true", help="plot run")
    args = parser.parse_args()

    if args.full:
        test_hindcast_output_dir = r'D:\test_hindcasts_examples_full'
        OTrun_root_output_dir = r'D:\OceanTrackerOutput\test_hindcast_readers_full'
    else:
        test_hindcast_output_dir= path.join(path.dirname(__file__),'unit_tests','data', 'hindcasts')
        OTrun_root_output_dir = r'D:\OceanTrackerOutput\test_readers_full_small'


    readers= [schism(args),GLORYS(args),ROMS(args)]
    #fTrereaders= [schism(args)]#

    for nr, reader in enumerate(readers):
        if args.type > -1 and args.type != nr: continue
        for nv, i in enumerate(reader):
            if args.variant > -1 and args.variant != nv: continue

            i = get_required_var_names(i, args)
            i['output_dir'] = test_hindcast_output_dir # where to put compressed hindcast
            if not args.write_off:
                write_files(i, args)

            if args.run_off:
                case_info_file_name= path.join(OTrun_root_output_dir, i['name'], i['name'] + '_caseInfo.json')
            else:
                # test run case
               case_info_file_name= run(i, OTrun_root_output_dir, args)

            if args.plot:
                from matplotlib import pyplot as plt
                from oceantracker.plot_output import plot_tracks
                from oceantracker.read_output.python import load_output_files
                tracks = load_output_files.load_track_data(case_info_file_name)
                # animate particles
                anim = plot_tracks.animate_particles(tracks, axis_lims=None, title='Minimal OceanTracker example',
                                                     show_dry_cells=True, show_grid=True,
                                                     )  # use ipython to show video, rather than matplotlib plt.show()

    pass
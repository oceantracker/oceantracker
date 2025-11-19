import numpy as np
from glob import glob
from copy import deepcopy
from os import path, makedirs, remove
import argparse
import xarray as xr
from oceantracker.util import class_importer_util, parameter_checking, message_logger, json_util
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
                'water_depth','A_Z_profile',]:
        add_var('required_vars',i, fmap, v)

    # add possible optional scalar vars
    for v in   ['water_temperature','salinity']:  add_var('optional_vars',i, fmap, v)

    # required grid variables
    for v in ['x','y','z_interface']:  add_var('required_vars',i, params['grid_variable_map'], v)

    # required integer variables from grid
    for v in ['bottom_interface_index','is_dry_cell']:  add_var('required_int_vars', i, params['grid_variable_map'], v)

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
    return i

def get_catalog(i, args):
    # find all variables in each file, sort in time order

    file_list= glob(path.join(i['input_dir'],'**',  i['file_mask']),recursive=True)
    file_list = np.asarray(file_list)
    vars={}
    f_start_retimes =[]
    for fileID,f in enumerate(file_list):

        # assumes time in every file
        #nc = NetCDFhandler(f)
        #nc.close()
        ds = xr.open_dataset(f, decode_times=False, decode_coords=False,decode_timedelta=False)

        # note time dim as time may not be in all files
        if i['time_var'] in ds.variables :  i['dims']['time'] = ds[i['time_var']].dims[0]

        t0 =float(ds[i['time_var']].compute().data[0])
        t1 = float(ds[i['time_var']].compute().data[0])

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



def _ensure_int(data):
    if np.issubdtype(data.dtype, np.floating):
        sel = np.isnan(data)
        data[sel] = missing_int
        data = data.astype(np.int32)  # zero based indcies for python
    return data

def get_triangulation(i, required_files) :
    # get triangulations and nodes inside axis_lims
    grid = i['grid']

    # find first file with node coords
    for name, v in required_files :
        ds = xr.open_dataset(name, decode_times=False, decode_coords=False,decode_timedelta=False)
        if grid['x_node'] in ds.variables: break

    x = ds[grid['x_node']].compute().data
    y = ds[grid['y_node']].compute().data
    tri = _ensure_int(ds[grid['triangulation']].compute().data) - int(i['one_based'])

    # find  triangles in sub-domain
    x_tri = np.mean(x[tri[:, :3]], axis=1)
    y_tri = np.mean(y[tri[:, :3]], axis=1)

    ax = i['axis_limits']
    sel_tri = np.logical_and.reduce((x_tri > ax[0], x_tri < ax[1], y_tri > ax[2], y_tri < ax[3]))
    sel_tri = np.flatnonzero(sel_tri)

    required_tri = tri[sel_tri, :]

    required_nodes=np.unique(required_tri[required_tri >=0])
    required_nodes = np.sort(required_nodes)

    new_triangulation = np.full((sel_tri.shape[0],4),missing_int,np.int32)
    for n, val in enumerate(required_nodes.tolist()):
        sel = int(val) == required_tri # where tri matches the required nodes
        new_triangulation[sel]= n +  int(i['one_based'])

    new_triangulation[new_triangulation < 0 ] = -1 # make missing 4th values the same

    if False:
        import matplotlib.pyplot as plt
        plt.triplot(x, y, tri[:,:3], c=[.8,.8,.8], lw=.5)
        plt.scatter(ax[0], ax[2], c='r')
        plt.scatter(ax[1], ax[3], c='g')
        if 'coast_point' in i:
            plt.scatter(i['coast_point'][0], i['coast_point'][1], marker='x', c='g')
        if 'deep_point' in i:
            plt.scatter(i['deep_point'][0], i['deep_point'][1],marker='x', c='g')
        xy=plt.ginput(2)
        print(xy)
        plt.show()


    return dict(required_cells=sel_tri,required_nodes=required_nodes,
                new_triangulation=new_triangulation,
                triangulation_dims= ds[grid['triangulation']].dims)

def write_files(i, required_files, args):

    out_dir = path.join(i['output_dir'],f'{i["name"]}')
    if not path.exists(out_dir):
        makedirs(out_dir)
    else:
        # delete old files
        for f in glob(out_dir+'/*'):
            remove(f)

    if 'dim_slices' not in i: i['dim_slices'] = {}
    dims = i['dims']

    # find file with coords and get new triangulation
    if not i['structured']:
        # set up slices for unstructured grid
        info = get_triangulation(i, required_files)
        i['dim_slices'][dims['node']] = info['required_nodes']
        i['dim_slices'][dims['cell']] = info['required_cells']
        print('cpmpressed: unstructured grid  nodes = ', info['required_nodes'].size, 'cells', info['required_cells'].size,)

    required_files = [ [n,]+r for n, r in enumerate(required_files)]# add index to order info to required_files
    order = np.random.choice(len(required_files), len(required_files), replace=False)


    for nn, o in enumerate(order):
        ID, file, vars = required_files[o]
        ds = xr.open_dataset(file, decode_times=False, decode_coords=False,decode_timedelta=False)
        print('starting file: ', path.basename(file))
        ds_out = xr.Dataset()

        # copy attributes
        for name, val in ds.attrs.items(): ds_out.attrs[name] = val

        dims = i['dims']

        copy_vars = i['required_vars'] + i['required_int_vars']
        # add first optional if found
        for v in i['optional_vars']:
            if v in ds.variables:
                copy_vars.append(v)
                break

        encoding = {}
        grid = i['grid']
        # add triangulation if present
        if grid['triangulation'] in ds.variables:
            ds_out[grid['triangulation']] = xr.DataArray(info['new_triangulation'], dims=info['triangulation_dims'])

        # loop over vars
        for v in copy_vars:
            if v not in ds.variables: continue
            print('\t\t compressing var=', v)
            data= ds[v].compute()
            # loop over all slicing
            for dim,s  in i['dim_slices'].items():
                if dim  in data.dims:

                    data= data.isel({dim:s})

            if v in i['required_int_vars']: data.data = _ensure_int(data.data)

            # compress time varying floats
            if dims['time'] in  data.dims and np.issubdtype(data,np.floating):
                scale_factor, add_offset, missing_value = compute_scale_and_offset_int16(data, missing_value=None)
                encoding[v] = dict(scale_factor=scale_factor, add_offset=add_offset, missing_value=missing_value,
                               dtype=np.int16,  zlib=True, complevel=9 )
            ds_out[v] = data.compute()

        #  time decimate whole dataset, wont work on one time st
        if dims['time'] in ds_out.dims:
            ds_out = ds_out.isel( {dims['time'] : slice(None, None, i['time_decimation'])}).compute()

        fn = path.join(out_dir,   f'{i["name"]}_{nn:03d}_time_order{ID:03d}.nc')

        if len(ds_out.variables) > 0:
            print('\t writing file: ', path.basename(fn))
            ds_out.to_netcdf(fn, encoding=encoding)
            print('\t\t done file: ', fn, list( ds.variables.keys()))
        pass

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
    ot.settings(root_output_dir=output_dir, output_file_base=file_base, time_step=10*60)
    ot.add_class('reader', input_dir=input_dir, file_mask=file_base + '*.nc')

    info = json_util.read_JSON(path.join(input_dir, 'info.json'))

    pulse_size= 10000 if args.full else 10
    if 'deep_point' in info:
        ot.add_class('release_groups', points=info['deep_point'],
                     release_interval=30*60, pulse_size=pulse_size, name='deep_point', )
    if 'coast_point' in info:
        ot.add_class('release_groups', points=info['coast_point'],
                     release_interval=30*60, pulse_size=pulse_size, name='coast_point' )
    case_info_file_name= ot.run()
    return case_info_file_name


def schism(args):
    # schism variants
    #todo hgrid file?
    base = dict(structured=False, one_based=True,)
    schism3D = deepcopy(base)
    schism3D.update( name='schism3D',  time_decimation=2,is3D=True,
                    axis_limits =  1.0e+06 *np.asarray([ 1.5903,    1.6026,    5.4795,    5.501]), # abel tasman
                    input_dir =r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD\2012',
                    file_mask= r'schism_marl201201*.nc',
                    class_name= 'oceantracker.reader.SCHISM_reader.SCHISMreader',
                    deep_point=[1594000, 5484200, -2],
                          )

    schism3Dv5 = deepcopy(base)
    dx = 0.05
    schism3Dv5.update(name='schism3D_v5', is3D=True,
           class_name='oceantracker.reader.SCHISM_reader_v5.SCHISMreaderV5',
           time_decimation=1,
           input_dir=r'F:\Hindcast_reader_tests\Schimsv5\HaurakiGulfv5\01',
            file_mask = r'*.nc',
            axis_limits=[175-dx,175.18+dx,-36.4-dx,-36.125+dx],
            deep_point=[175.1, -36.3, -2],
            coast_point=[175.05, -36.225] )

    return [schism3D, schism3Dv5]

def GLORYS(args):
    # schism variants
    #todo hgrid file?
    base = dict(structured=True, one_based=True)
    schism3D = deepcopy(base)
    schism3D.update( name='GLORYS3Dsigma',  time_decimation=2,is3D=True,
                    axis_limits =  1.0e+06 *np.asarray([ 1.5903,    1.6026,    5.4795,    5.501]), # abel tasman
                    input_dir =r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD\2012',
                    file_mask= r'schism_marl201201*.nc',
                    class_name= 'oceantracker.reader.SCHISM_reader.SCHISMreader',
                    deep_point=[1594000, 5484200, -2],
                     )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple script to greet a user.")
    parser.add_argument('-full',   action="store_true",  help="long demo hindcasts"    )
    parser.add_argument('-type', type=int, default=-1)
    parser.add_argument('-variant', type=int, default=-1)
    parser.add_argument('-run_off', action="store_true", help=" toggle run demo hindcasts off ")
    parser.add_argument('-write_off', action="store_true", help="toggle write hindcast off")
    parser.add_argument('-plot', action="store_true", help="plot run")
    args = parser.parse_args()


    test_hindcast_out_dir_default  =  path.join(path.dirname(__file__), 'hindcasts')

    if args.full:
        test_hindcast_output_dir = r'F:\H_Local_drive\ParticleTracking\unit_test_full_hindcasts'
        run_output_dir = r'D:\OceanTrackerOutput\test_hindcast_readers_full'
    else:
        test_hindcast_output_dir= path.join(path.dirname(__file__),'unit_tests','data', 'hindcasts')
        run_output_dir = r'D:\OceanTrackerOutput\test_hindcast_readers_small'

    readers= [schism(args)]
    for nr, reader in enumerate(readers):
        if args.type > -1 and args.type != nr: continue
        for nv, i in enumerate(reader):
            if args.variant > -1 and args.variant != nv: continue

            i = get_required_var_names(i, args)
            i['output_dir'] = test_hindcast_output_dir
            required_files= get_catalog(i,args) # find all variables in each file, sort in time order
            if not args.write_off:
                write_files(i, required_files, args)

            if args.run_off:
                case_info_file_name= path.join(run_output_dir,i['name'],i['name']+'_caseInfo.json')
            else:
                # test run case
               case_info_file_name= run(i, run_output_dir,args)


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
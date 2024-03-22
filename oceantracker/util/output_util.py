# add attributes mapping release index to release group name
import numpy as np
from oceantracker.util.ncdf_util import NetCDFhandler
from os import path
from oceantracker.shared_info import SharedInfo as si
def add_release_group_ID_info_to_netCDF(nc, release_groups):
    # add a maps of release group as attributes  index to net ndf
    # plus release points /points of polygon

    if nc is None: return # file already closed
    max_points= 0
    for n, name in enumerate(release_groups.keys()):
        nc.write_global_attribute(f'release_groupID_{name}', n)
        max_points= max(max_points, release_groups[name].points.shape[0] if hasattr(release_groups[name],'points') else release_groups[name].params['points'].shape[0])

    # make array full on points with different lengths for each release group
    n_rel= len(release_groups)
    points     = np.full((n_rel,max_points,3),0.,dtype= np.float64)
    n_points   = np.full((n_rel, ), 0, dtype=np.int32)
    is_polygon = np.full((n_rel,), 0, dtype=np.int8)
    
    for n, name in enumerate(release_groups.keys()):
        r = release_groups[name]
        p = r.points if hasattr(r,'points') else r.params['points']
        points[n,:p.shape[0],:p.shape[1]] = p
        n_points[n] = p.shape[0]
        is_polygon[n] = r.info['release_type'] == 'polygon'

    nc.write_a_new_variable('release_points', points, ['release_group_dim','max_points_dim','components'], description='release points or points comprising polygon')
    nc.write_a_new_variable('number_of_release_points', n_points, ['release_group_dim'], description='number of points in each relase group')
    nc.write_a_new_variable('is_polygon_release', is_polygon, ['release_group_dim'], description=' =1 if release group is a polygon, 0 if point release')

def add_particle_status_values_to_netcdf(nc):
    # write status values to file as attributes
    for key, val in si.particle_status_flags.as_dict().items():
        nc.write_global_attribute('status_' + key, int(val))

def write_release_group_netcdf():
    '''Write releae groups data to own file for each case '''
    fn =  si.run_info.output_file_base + '_release_group_info.nc'
    nc = NetCDFhandler(path.join(si.run_info.run_output_dir, fn), mode= 'w')

    # loop over release groups
    for name, rg in si.roles.release_groups.items():

        ID = rg.info['instanceID']
        v_name = f'ReleaseGroup_{ID:04d}'
        dim_name = f'rg_{ID:04d}'

        if rg.info['release_type'] in  ['point', 'polygon']:
            v_name += '_points'
            points = rg.params['points']
            is3D = points.shape[1] ==3
            dims = [dim_name + '_points', 'vector3D' if is3D else 'vector2D']

        elif rg.info['release_type'] in ['grid']:
            v_name += '_grid'
            points =  rg.info['x_grid']
            dims = [dim_name +'_rows', dim_name +'_cols', 'vector2D']
            is3D = False
        else:
            raise('write_release_group_netcdf> unknows release group type')

        nc.add_dimension(dim_name,points.shape[0])
        sc = rg.release_scheduler.info
        attr= dict(release_type=rg.info['release_type'], is3D = is3D,
                    release_group_name = name, instanceID= rg.info['instanceID'], pulses= rg.info['pulseID'],
                    start =sc['start_time'], end =sc['end_time'], start_date= sc['start_date'], end_date =sc['end_date'],)
        nc.write_a_new_variable(v_name, points, dims, units='meters or decimal deg. as  (lon, lat)',  attributes=attr)
    
    nc.close()
    return fn
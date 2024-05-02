# add attributes mapping release index to release group name
import numpy as np
from oceantracker.util.ncdf_util import NetCDFhandler
from os import path
from oceantracker.shared_info import SharedInfo as si

def add_particle_status_values_to_netcdf(nc):
    # write status values to file as attributes
    for key, val in si.particle_status_flags.as_dict().items():
        nc.write_global_attribute('status_' + key, int(val))

def write_release_group_netcdf():
    '''Write release groups data to own file for each case '''
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
            raise('write_release_group_netcdf> unknown release group type')

        nc.add_dimension(dim_name,points.shape[0])
        sc = rg.release_scheduler.info
        attr= dict(release_type=rg.info['release_type'], is3D = is3D,
                    release_group_name = name, instanceID= rg.info['instanceID'], pulses= rg.info['pulseID'],
                    start =sc['start_time'], end =sc['end_time'], start_date= sc['start_date'], end_date =sc['end_date'],)
        nc.write_a_new_variable(v_name, points, dims, units='meters or decimal deg. as  (lon, lat)',  attributes=attr)
    
    nc.close()
    return fn


def add_polygon_list_to_group_netcdf(nc,polygon_list):
    '''Write poygon in the file groups data to own file for each case '''
    # loop over polygon_list
    for ID, p in  enumerate(polygon_list):

        v_name = f'Polygon_{ID:04d}'
        dim_name = f'poly_{ID:04d}'
        points = np.asarray(p['points'])
        nc.add_dimension(dim_name, points.shape[0])
        attr = dict(user_polygonID=p['user_polygonID'] if 'user_polygonID' in p else 0 , instanceID=ID,
                    polygon_name=f'polygon{ID:04d}' if p['name'] is None else p['name'])
        nc.write_a_new_variable(v_name, points, [dim_name,'vector2D'],
                                units='meters or decimal deg. as  (lon, lat)',
                                description='stats ploygon cords',
                                attributes=attr)
    pass

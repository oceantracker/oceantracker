# add attributes mapping release index to release group name
import numpy as np
from oceantracker.util.ncdf_util import NetCDFhandler
from os import path
from oceantracker.shared_info import shared_info as si

def add_particle_status_values_to_netcdf(nc):
    # write status values to file as attributes
    for key, val in si.particle_status_flags.items():
        nc.write_global_attribute('status_' + key, int(val))

def write_release_group_netcdf():
    '''Write release groups data to own file for each case '''
    fn =  si.run_info.output_file_base + '_release_groups.nc'
    nc = NetCDFhandler(path.join(si.run_info.run_output_dir, fn), mode= 'w')
    nc.write_global_attribute('geographic_coords', int(si.settings.use_geographic_coords))

    # loop over release groups
    for name, rg in si.class_roles.release_groups.items():

        ID = rg.info['instanceID']
        v_name = f'ReleaseGroup_{ID:04d}'
        dim_name = f'rg_{ID:04d}'


        v_name += '_points'
        points = rg.params['points']
        is3D = points.shape[1] ==3
        dims = [dim_name + '_points', 'vector3D' if is3D else 'vector2D']


        nc.add_dimension(dim_name,points.shape[0])

        sc = rg.schedulers['release'].info
        # add useful info to variable atributes
        attr= dict(release_type=rg.info['release_type'], is3D = is3D,
                   release_group_name = name, instanceID= rg.info['instanceID'], pulses= rg.info['pulseID'],
                   pulse_size =rg.params['pulse_size'],
                   release_interval=rg.params['release_interval'],
                   start =sc['start_time'], end =sc['end_time'], start_date= sc['start_date'], end_date =sc['end_date'],
                   max_age = si.info.large_float if rg.params['max_age'] is None else rg.params['max_age'],
                   user_release_groupID=rg.params['user_release_groupID'],
                   user_release_group_name= rg.params['user_release_group_name'],
                   number_released= rg.info['number_released'])

        if rg.info['release_type'] == 'radius':
            attr.update(radius=rg.params['radius'])

        nc.write_a_new_variable(v_name, points, dims, units='meters or decimal deg. as  (lon, lat)',
                                description='release locations, not outside grid', attributes=attr)


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

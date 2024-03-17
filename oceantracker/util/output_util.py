# add attributes mapping release index to release group name
import numpy as np
from oceantracker.common_info_default_param_dict_templates import  particle_info
def add_release_group_ID_info_to_netCDF(nc, release_groups):
    # add a maps of release group as attributes  index to net ndf
    # plus release points /points of polygon

    if nc is None: return # file already closed
    max_points= 0
    for n, name in enumerate(release_groups.keys()):
        nc.write_global_attribute(f'release_groupID_{name}', n)
        max_points= max(max_points, release_groups[name].points.shape[0])

    # make array full on points with different lengths for each release group
    n_rel= len(release_groups)
    points     = np.full((n_rel,max_points,3),0.,dtype= np.float64)
    n_points   = np.full((n_rel, ), 0, dtype=np.int32)
    is_polygon = np.full((n_rel,), 0, dtype=np.int8)
    
    for n, name in enumerate(release_groups.keys()):
        r = release_groups[name]
        p = r.points
        points[n,:p.shape[0],:p.shape[1]] = p
        n_points[n] = p.shape[0]
        is_polygon[n] = r.info['release_type'] == 'polygon'

    nc.write_a_new_variable('release_points', points, ['release_group_dim','max_points_dim','components'], description='release points or points comprising polygon')
    nc.write_a_new_variable('number_of_release_points', n_points, ['release_group_dim'], description='number of points in each relase group')
    nc.write_a_new_variable('is_polygon_release', is_polygon, ['release_group_dim'], description=' =1 if release group is a polygon, 0 if point release')

def add_particle_status_values_to_netcdf(nc):
    # write status values to file as attributes
    for key, val in particle_info['status_flags'].items():
        nc.write_global_attribute('status_' + key, int(val))
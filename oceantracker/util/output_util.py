# add attributes mapping release index to release group name
import numpy as np

def add_release_group_ID_info_to_netCDF(nc, prg):
    # add a maps of release group as attributes  index to net ndf
    # plus release points /points of polygon


    if nc is None: return # file already closed

    max_points= 0
    for n, name in enumerate(prg.keys()):
        nc.write_global_attribute(f'release_groupID_{name}', n)
        max_points= max(max_points, prg[name].params['points'].shape[0])

    # make array full on points with different lengths for each release group
    n_rel= len(prg)
    points     = np.full((n_rel,max_points,3),0.,dtype= np.float64)
    n_points   = np.full((n_rel, ), 0, dtype=np.int32)
    is_polygon = np.full((n_rel,), 0, dtype=np.int8)
    
    for n, name in enumerate(prg.keys()):
        r = prg[name]
        p = r.params['points']
        points[n,:p.shape[0],:p.shape[1]] = p
        n_points[n] = p.shape[0]
        is_polygon[n] = r.info['release_type'] == 'polygon'

    nc.write_a_new_variable('release_points', points, ['release_group_dim','max_points_dim','components'], description='release points or points comprising polygon')
    nc.write_a_new_variable('number_of_release_points', n_points, ['release_group_dim'], description='number of points in each relase group')
    nc.write_a_new_variable('is_polygon_release', is_polygon, ['release_group_dim'], description=' =1 if release group is a polygon, 0 if point release')


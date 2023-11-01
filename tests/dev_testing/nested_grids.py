import matplotlib.pyplot as plt
import numpy as np
from oceantracker.util import  ncdf_util, triangle_utilities_code, polygon_util

from oceantracker.reader.schism_reader import read_hgrid_file

def read_hydo_model(file_name, hgrid_file):
    nc = ncdf_util.NetCDFhandler(file_name)
    d = nc.read_variables(['SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y','SCHISM_hgrid_face_nodes','depth','node_bottom_index'])
    d.update(dict(x=np.stack( ( d['SCHISM_hgrid_node_x'],d['SCHISM_hgrid_node_y']), axis=1),
              triangles= d['SCHISM_hgrid_face_nodes']-1)
             )
    d['is_open_boundary_node']=  read_hgrid_file(hgrid_file)
    return d


def build_grid(grid):
    grid['node_to_tri_map'], grid['tri_per_node'] = triangle_utilities_code.build_node_to_triangle_map(grid['triangles'][:,:3], grid['x'])
    grid['adjacency'] = triangle_utilities_code.build_adjacency_from_node_tri_map(grid['node_to_tri_map'], grid['tri_per_node'], grid['triangles'][:,:3])
    grid['is_boundary_triangle'] = triangle_utilities_code.get_boundary_triangles(grid['adjacency'])
    grid['grid_outline'] = triangle_utilities_code.build_grid_outlines(grid['triangles'][:,:3], grid['adjacency'],
                                                                       grid['is_boundary_triangle'], grid['node_to_tri_map'], grid['x'])
    return  grid

def merge_grids(outer,h2):


    # find tri of outer grid inside inner grid
    P = polygon_util.InsidePolygon(h2['grid_outline']['domain']['points'])

    # find triangles of outer grid where all nodes are outside inner grid
    merged = {}
    merged['outer_triangles_to_keep'] = np.full((outer['triangles'].shape[0],),True)
    for m in range(3):
        nodes= outer['triangles'][:, m]
        x =  outer['x'][nodes, :] # cords of each vertex
        sel = P.is_inside(x)
        merged['outer_triangles_to_keep'][sel] = False # dont keep triangle with if any vertex node inside inner grid

    tri_reduced_outer_grid = outer['triangles'][merged['outer_triangles_to_keep'], :] # triangulation of kept triangles
    merged['outer_grid_nodes_to_keep']  = np.sort(np.unique(tri_reduced_outer_grid))

    # build merged grid with outer grid last
    merged['x'] = np.vstack((h2['x'], outer['x'][merged['outer_grid_nodes_to_keep'] ,:]))
    map_outer_old_to_new_nodes = np.full((outer['x'].shape[0],),-1, dtype=np.int32)
    map_outer_old_to_new_nodes[ merged['outer_grid_nodes_to_keep']] = np.arange( merged['outer_grid_nodes_to_keep'].size)
    map_outer_old_to_new_nodes +=  merged['x'].size # offset node map for ends

    # replace old outer node numbers with those in merged grid
    for m in range(3):
        tri_reduced_outer_grid[:,m] = map_outer_old_to_new_nodes[tri_reduced_outer_grid[:,m]]
    merged['triangles'] = np.vstack((h2['triangles'], tri_reduced_outer_grid))
    return merged

if __name__ == "__main__":

    h1 = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2010\01\NZfinite20100101_01z.nc'
    o1 = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\hgridNZ_run.gr3'

    h2 = r'F:\Hindcasts\2019_portGoreHydroModelKingSalmon\schout_Dec1.nc'
    o2 = r'F:\Hindcasts\2019_portGoreHydroModelKingSalmon\hgrid.gr3'

    h1 = read_hydo_model(h1, o1)
    h1 = build_grid(h1)
    h2 = read_hydo_model(h2,o2)
    h2 = build_grid(h2)

    merged = merge_grids(h1,h2)

    plt.triplot(h1['x'][:,0],h1['x'][:,1], h1['triangles'][:,:3])
    plt.triplot(h2['x'][:, 0], h2['x'][:, 1], h2['triangles'][:, :3])
    xy = h2['grid_outline']['domain']['points']
    plt.plot(xy[:, 0], xy[:, 1], 'r')
    plt.show()

    plt.triplot(merged['x'][:, 0], merged['x'][:, 1], merged['triangles'][:, :3])
    plt.show()
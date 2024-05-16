import matplotlib.pyplot as plt
import numpy as np
from oceantracker.util import  ncdf_util, triangle_utilities, polygon_util
from oceantracker.interpolator.util import triangle_interpolator_util
from oceantracker.reader.schism_reader import read_hgrid_file
from numba import njit
from scipy import spatial
def read_hydo_model(file_name, hgrid_file):
    nc = ncdf_util.NetCDFhandler(file_name)
    d = nc.read_variables(['SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y','SCHISM_hgrid_face_nodes','depth','node_bottom_index'])
    d.update(dict(x=np.stack( ( d['SCHISM_hgrid_node_x'],d['SCHISM_hgrid_node_y']), axis=1),
              triangles= d['SCHISM_hgrid_face_nodes']-1)
             )
    d['hgrid'] =  read_hgrid_file(hgrid_file)
    return d


def build_grid(grid):
    grid['node_to_tri_map'], grid['tri_per_node'] = triangle_utilities.build_node_to_triangle_map(grid['triangles'][:,:3], grid['x'])
    grid['adjacency'] = triangle_utilities.build_adjacency_from_node_tri_map(grid['node_to_tri_map'], grid['tri_per_node'], grid['triangles'][:,:3])
    grid['is_boundary_triangle'] = triangle_utilities.get_boundary_triangles(grid['adjacency'])
    grid['grid_outline'] = triangle_utilities.build_grid_outlines(grid['triangles'][:,:3], grid['adjacency'],
                                                                       grid['is_boundary_triangle'], grid['node_to_tri_map'], grid['x'])

    return  grid


def triangles_with_points_inside(x_grid, triangles, x_query,  bc_walk_tol=0.00):
    @njitOT
    def _work(nis):
        bc = np.full((3,), -1, dtype=np.float64)
        for ntri in range(n_tri):
            for n_xq in range(x_query.shape[0]):  # loop over query triangles
                n_min, n_max = triangle_interpolator_util._get_single_BC_cord_numba(x_query[n_xq,:], BCtransform[ntri, :, :], bc)
                if bc[n_min] > -bc_walk_tol and bc[n_max] < 1. + bc_walk_tol:
                    nis[ntri] = True


    BCtransform = triangle_interpolator_util.get_BC_transform_matrix(x_grid, triangles)
    n_tri = BCtransform.shape[0]
    node_inside= np.full((triangles.shape[0],),False)

    _work(node_inside)

    return node_inside

def find_points_inside_triangles(x_grid, triangles, x_query,  bc_walk_tol=0.00):
    @njitOT
    def _work(nis):
        bc = np.full((3,), -1, dtype=np.float64)
        for ntri in range(n_tri):
            for n_xq in range(x_query.shape[0]):  # loop over query triangles
                n_min, n_max = triangle_interpolator_util._get_single_BC_cord_numba(x_query[n_xq,:], BCtransform[ntri, :, :], bc)
                if bc[n_min] > -bc_walk_tol and bc[n_max] < 1. + bc_walk_tol:
                    nis[n_xq] = True


    BCtransform = triangle_interpolator_util.get_BC_transform_matrix(x_grid, triangles)
    n_tri = BCtransform.shape[0]
    are_inside= np.full((x_query.shape[0],),False)

    _work(are_inside)

    return are_inside

@njitOT
def find_triangles_with_nodes(tri,nodes):
    out= np.full((tri.shape[0],), False)
    found=0
    for n_tri in range(tri.shape[0]):
        for n in nodes:
            if n in tri[n_tri,:]:
                out[n_tri] = True
                found += 1
                break
    return out

def merge_grids(outer,inner):
    #todo split quad cells of both grids first?
    merged={}

    # find any tri of outer grid with node inside inner grid
    P = polygon_util.InsidePolygon(inner['grid_outline']['domain']['points'])
    outer_nodes_inside_inner = np.full((outer['triangles'].shape[0],), 0,dtype=np.int32)
    for m in range(3):
        nodes = outer['triangles'][:, m]
        x = outer['x'][nodes, :]  # cords of each vertex
        sel = P.is_inside(x)
        outer_nodes_inside_inner[sel] += 1  # count nodes insicde inner

    merged['outer_triangles_to_keep'] =  np.flatnonzero(outer_nodes_inside_inner==0)
    merged['outer_triangles_overlapping'] = np.flatnonzero(np.logical_or(outer_nodes_inside_inner== 1, outer_nodes_inside_inner == 2))


    # now find triangles of outer grid with any node of inner grids open boundary
    sel = triangles_with_points_inside(outer['x'], outer['triangles'][ merged['outer_triangles_overlapping'] ,:], inner['x'][inner['hgrid']['node_type']==2,:])
    merged['outer_triangles_overlapping']= merged['outer_triangles_overlapping'][sel] # only keep those with open bondary node

    # now need to remove any remaining outer triangles  which have a land boundary node of inner grid inside them
    sel = triangles_with_points_inside(outer['x'], outer['triangles'][  merged['outer_triangles_to_keep'], :], inner['x'][inner['hgrid']['node_type']==1, :])
    merged['outer_triangles_to_keep'] = merged['outer_triangles_to_keep'][~sel]  # only keep those without open boundary node



    # now find nodes in common between those being keeps of out and the node of overlaping region
    nodes_outer =   np.unique( outer['triangles'][merged['outer_triangles_to_keep'],:])
    nodes_outer = nodes_outer[nodes_outer >=0]  # get rid  of quad cell mask
    nodes_overlap = np.unique( outer['triangles'][merged['outer_triangles_overlapping'], :]) #
    nodes_overlap = nodes_overlap[nodes_overlap >= 0]
    outer_shared_edge_nodes = np.intersect1d(nodes_overlap,nodes_outer) # shared nodes of outer grid and intersection grid

    # discard the closest triangles of the outer grid to give larger transition

    #    first find triangles of non-overlaping outer girid which have shared nodes with overlap
    sel = find_triangles_with_nodes(outer['triangles'][merged['outer_triangles_to_keep'],:],outer_shared_edge_nodes)
    merged['outer_triangles_to_keep'] = merged['outer_triangles_to_keep'][~sel]

    #   refind edge outer nodes
    nodes_outer = np.unique(outer['triangles'][merged['outer_triangles_to_keep'], :])
    nodes_outer = nodes_outer[nodes_outer >= 0]  # get rid  of quad cell mask

    #   new overlap nodes without additionsal layer
    sel = triangles_with_points_inside(outer['x'], outer['triangles'][merged['outer_triangles_to_keep'], :], inner['x'][inner['hgrid']['node_type'] == 1, :])
    merged['outer_triangles_to_keep'] = merged['outer_triangles_to_keep'][~sel]  # only keep those without open boundary node
    nodes_overlap = np.unique( outer['triangles'][merged['outer_triangles_overlapping'], :]) #
    nodes_overlap = nodes_overlap[nodes_overlap >= 0]

    outer_shared_edge_nodes = np.intersect1d(nodes_overlap, nodes_outer)  # shared nodes of outer grid and intersection grid

    # keep  inner nodes not inside transion zone
    inner_shared_edge_nodes =  np.flatnonzero( inner['hgrid']['node_type'] == 2) # open bounadry nodes
    sel = find_points_inside_triangles(outer['x'], outer['triangles'][ merged['outer_triangles_overlapping'], :], inner['x'][inner_shared_edge_nodes, :])
    inner_shared_edge_nodes= inner_shared_edge_nodes[sel]  # only keep those without open boundary node

    # build transitional triangulation
    x_outer=outer['x'][outer_shared_edge_nodes,:] # location of outer nodes of merged area
    x_inner= inner['x'][inner_shared_edge_nodes,:] # location of inner nodes of merged area
    x_combined= np.vstack((x_outer,x_inner))
    is_outer_node= np.full_like(x_combined,False)
    is_outer_node[:x_outer.shape[0]] =True
    DT= spatial.Delaunay(x_combined) # convex hull triangulation
    tri_transion =DT.vertices

    # get interior of transition triangulation by discarding triangles which have all outer or inner nodes
    node_type= np.full((DT.points.shape[0],),False)

    node_type[x_outer.shape[0]:] = True # mark nodes from inner grid
    tri_node_type = node_type[tri_transion]
    keep = ~np.all(tri_node_type,axis=1)
    #keep[~np.all(~tri_node_type,axis=1)] = False # remove those with all

    tri_transion= tri_transion[keep,:] # discard exterior triangles


    plt.triplot(inner['x'][:, 0], inner['x'][:, 1], inner['triangles'][:, :3],lw=.5,c=[.8,.8,.8])
    plt.triplot(outer['x'][:,0],  outer['x'][:,1], outer['triangles'][merged['outer_triangles_to_keep'],:3],lw=.5)
    plt.triplot(outer['x'][:, 0], outer['x'][:, 1],outer['triangles'][merged['outer_triangles_overlapping'], :3],lw=.5)

    #plt.triplot(x_combined[:,0],x_combined[:,1], tri_transion,c='r', lw=.5)


    plt.plot( outer['x'][outer_shared_edge_nodes,0],  outer['x'][outer_shared_edge_nodes,1], 'go')
    plt.plot(inner['x'][inner_shared_edge_nodes, 0], inner['x'][inner_shared_edge_nodes, 1], 'ro')

    plt.show(block=True)





    tri_reduced_outer_grid = outer['triangles'][merged['outer_triangles_to_keep'], :] # triangulation of kept triangles

    merged['outer_grid_nodes_to_keep']  = np.sort(np.unique(tri_reduced_outer_grid))

    # build merged grid with outer grid last
    merged['x'] = np.vstack((inner['x'], outer['x'][merged['outer_grid_nodes_to_keep'] ,:]))
    map_outer_old_to_new_nodes = np.full((outer['x'].shape[0],),-1, dtype=np.int32)
    map_outer_old_to_new_nodes[ merged['outer_grid_nodes_to_keep']] = np.arange( merged['outer_grid_nodes_to_keep'].size)
    map_outer_old_to_new_nodes +=  merged['x'].size # offset node map for ends

    # replace old outer node numbers with those in merged grid
    for m in range(3):
        tri_reduced_outer_grid[:,m] = map_outer_old_to_new_nodes[tri_reduced_outer_grid[:,m]]
    merged['triangles'] = np.vstack((inner['triangles'], tri_reduced_outer_grid))
    return merged



if __name__ == "__main__":

    outer_grid = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\2010\01\NZfinite20100101_01z.nc'
    o1 = r'G:\Hindcasts_large\OceanNumNZ-2022-06-20\final_version\hgridNZ_run.gr3'

    h2 = r'F:\Hindcasts\2019_portGoreHydroModelKingSalmon\schout_Dec1.nc'
    o2 = r'F:\Hindcasts\2019_portGoreHydroModelKingSalmon\hgrid.gr3'

    #h2=r'F:\Hindcasts\Whangarei_31122012_wtemp_3D.nc'

    outer_grid = read_hydo_model(outer_grid, o1)
    outer_grid = build_grid(outer_grid)


    h2 = read_hydo_model(h2,o2)
    h2 = build_grid(h2)

    merged = merge_grids(outer_grid,h2)

    plt.triplot(outer_grid['x'][:,0],outer_grid['x'][:,1], outer_grid['triangles'][:,:3])
    plt.triplot(h2['x'][:, 0], h2['x'][:, 1], h2['triangles'][:, :3])
    xy = h2['grid_outline']['domain']['points']
    plt.plot(xy[:, 0], xy[:, 1], 'r')
    plt.show()

    plt.triplot(merged['x'][:, 0], merged['x'][:, 1], merged['triangles'][:, :3])
    plt.show()
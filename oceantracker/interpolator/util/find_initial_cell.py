import numpy as np
from oceantracker.interpolator.util.triangle_interpolator_util import  check_if_point_inside_triangle_connected_to_node


def find_hori_cellKDtree(xq, grid, KDtree, bc_walk_tol):
    # find nearest cell to xq
    # find nearest node
    dist, nodes = KDtree.query(xq[:, :2])
    nodes = nodes.astype(np.int32)  # KD tree gives int64,need for compatibility of types

    # look in triangles attached to each node for tri containing each point,
    # if it is it must be inside the triangular grids domain
    is_inside_domain, n_cell, bc  = check_if_point_inside_triangle_connected_to_node(xq[:, :2], nodes,
                               grid['node_to_tri_map'], grid['tri_per_node'],
                            grid['bc_transform'] , bc_walk_tol)
    # if x is nan dist is infinite
    n_cell[~np.isfinite(dist)] = -1

    return n_cell, bc, is_inside_domain
import numpy as np
from numba import njit
from oceantracker.interpolator.util.interp_kernals import kernal_linear_interp1D

@njit
def get_node_layer_field_values(data, node_to_tri_map, tri_per_node,cell_center_weights):
    # get nodal values from data in surrounding cells based in distance weighting

    data_nodes = np.full((data.shape[0],) + (len(node_to_tri_map),) +(data.shape[2],) , 0., dtype=np.float32)

    for nt in range(data.shape[0]): # loop over time steps
        # loop over triangles
        for node in range(node_to_tri_map.shape[0]):
            for nz in range(data.shape[2]):
                # loop over cells containing this node
                for m in range(tri_per_node[node]):
                    cell = node_to_tri_map[node, m]
                    data_nodes[nt, node, nz] += data[nt, cell, nz]*cell_center_weights[node, m] # weight this cell value

    return data_nodes

@njit
def convert_layer_field_to_levels_from_fixed_depth_fractions(data, zfraction_center, zfraction_boundaries):
    # convert values at depth at center of the cell to values on the boundaries between cells baed on fractional layer/boundary depths
    data_levels = np.full((data.shape[0],) + (data.shape[1],) + (zfraction_boundaries.shape[0],), 0., dtype=np.float32)

    for nt in range(data.shape[0]):
        for n in range(data.shape[1]):
            for nz in range(1,data.shape[2]):
                # linear interp levels not, first or last boundary
                data_levels[nt, n, nz] = kernal_linear_interp1D(zfraction_center[nz - 1], data[nt, n, nz - 1], zfraction_center[nz], data[nt, n, nz], zfraction_boundaries[nz])

            # extrapolate to top zlevel
            data_levels[nt, n, -1] = kernal_linear_interp1D(zfraction_center[-2], data[nt, n, -2], zfraction_center[-1], data[nt, n, -1], zfraction_boundaries[-1])

            # extrapolate to bottom zlevel
            data_levels[nt, n, 0] = kernal_linear_interp1D(zfraction_center[0], data[nt, n, 0], zfraction_center[1], data[nt, n, 1], zfraction_boundaries[0])

    return data_levels

@njit
def convert_layer_field_to_levels_from_depth_fractions_at_each_node(data, zfraction_center, zfraction_boundaries):
    # convert values at depth at center of the cell to values on the boundaries between cells baed on fractional layer/boundary depths
    data_levels = np.full((data.shape[0],) + (data.shape[1],) + (zfraction_boundaries.shape[1],), 0., dtype=np.float32)

    for nt in range(data.shape[0]):
        for n in range(data.shape[1]):
            for nz in range(1,data.shape[2]):
                # linear interp levels not, first or last boundary
                data_levels[nt, n, nz] = kernal_linear_interp1D(zfraction_center[n, nz - 1], data[nt, n, nz - 1], zfraction_center[n, nz], data[nt, n, nz], zfraction_boundaries[n, nz])

            # extrapolate to top zlevel
            data_levels[nt, n, -1] = kernal_linear_interp1D(zfraction_center[n, - 2], data[nt, n, -2], zfraction_center[n, -1], data[nt, n, -1], zfraction_boundaries[n, -1])

            # extrapolate to bottom zlevel
            data_levels[nt, n, 0] = kernal_linear_interp1D(zfraction_center[n, 0], data[nt, n, 0], zfraction_center[n, 1], data[nt, n, 1], zfraction_boundaries[n, 0])

    return data_levels

@njit()
def calculate_cell_center_weights_at_node_locations(x_node, x_cell, node_to_tri_map, tri_per_node):
    # calculate distance weights for values at cell centers, to be used in interploting cell center values to nodal values
    weights= np.full_like(node_to_tri_map, 0.,dtype=np.float32)
    dxy= np.full((2,), 0.,dtype=np.float32)

    for n in range(x_node.shape[0]):
        s= 0.
        n_cells=tri_per_node[n]
        for m in range(n_cells):
            dxy[:] = x_cell[node_to_tri_map[n,m],:2] - x_node[n, :2]
            dist = np.sqrt(dxy[0]**2 + dxy[1]**2)
            weights[n,m] = dist
            s += dist

        # normalize weights
        for m in range(n_cells): weights[n,m]=weights[n,m] /s

    return  weights

import numpy as np
from numba import njit
from oceantracker.interpolator.util.interp_kernals import kernal_linear_interp1D
from copy import copy
from oceantracker.util.numba_util import njitOT
from oceantracker.util.triangle_utilities_code import split_quad_cells

def convert_regular_grid_to_triangles(grid,mask):
    # get nodes for each corner of quad
    rows = np.arange(mask.shape[0])
    cols = np.arange(mask.shape[1])

    # get global node numbers for flattened grid in C order, row 1 should be 0, 1, 3 ....
    # note rows are x, and cols y in ROMS which are Fortran ordered arrays
    grid['grid_node_numbers'] = cols.size * rows.reshape((-1, 1)) + cols.reshape((1, -1))

    # get global node numbers of triangle nodes
    n1 = grid['grid_node_numbers'][:-1, :-1]
    n2 = grid['grid_node_numbers'][:-1, 1:]
    n3 = grid['grid_node_numbers'][1:, 1:]
    n4 = grid['grid_node_numbers'][1:, :-1]

    # build Quad cellls
    quad_cells = np.stack((n1.flatten('C'), n2.flatten('C'), n3.flatten('C'), n4.flatten('C'))).T

    # keep  quad cells with less than 3 land nodes
    sel = np.sum(mask.flatten('C')[quad_cells], axis=1) < 3
    quad_cells = quad_cells[sel, :]

    grid['quad_cells_to_split'] = np.arange(quad_cells.shape[0]).astype(np.int32)
    grid['triangles'] = split_quad_cells(quad_cells, grid['quad_cells_to_split']).astype(np.int32)
    grid['active_nodes'] = np.unique(grid['triangles'])  # the nodes that are used in triangulation ( ie owithout land)

    return grid
@njitOT
def convert_zlevels_to_fractions(zlevels,bottom_cell_index,z0):
    # get zlevels as fraction of water depth
    z_fractions= np.full_like(zlevels,np.nan,dtype=np.float32)
    for n in range(zlevels.shape[0]): # loop over nodes
        z_surface = float(zlevels[n, -1])
        z_bottom= float(zlevels[n,bottom_cell_index[n]])
        total_water_depth = abs(z_surface-z_bottom)

        for nz in range(bottom_cell_index[n], zlevels.shape[1]):
            if total_water_depth > z0:
                z_fractions[n,nz] = (zlevels[n,nz]-z_bottom)/total_water_depth
            else:
                z_fractions[n, nz] = 0.
    return z_fractions

@njitOT
def find_node_with_smallest_bot_layer(z_fractions,bottom_cell_index):
    # find the  profile with thinest bottom layer as fraction of water depth  from layer boundary zlevels

    node_min= -1
    min_dz= np.inf
    for n in range(z_fractions.shape[0]): # loop over nodes

        dz_bot = z_fractions[n, bottom_cell_index[n] + 1] - z_fractions[n, bottom_cell_index[n]]

        if dz_bot > 0 and dz_bot < min_dz:
            min_dz = dz_bot
            node_min = n

    return node_min

@njitOT
def  interp_4D_field_to_fixed_sigma_values(zlevel_fractions,bottom_cell_index,sigma,
                                           water_depth,tide,z0,minimum_total_water_depth,
                                           data,out, is_water_velocity):
    # assumes time invariant zlevel_fractions, linear interp
    # set up space
    for nt in range(out.shape[0]):
        for node in range(out.shape[1]):
            nz_bottom =  int(bottom_cell_index[node])
            nz_data = nz_bottom
            # loop over new levels
            for nz in range(sigma.size-1):

                # if the sigma is above next zlevel, move data zlevel index up one
                nz_data +=  sigma[nz] > zlevel_fractions[node, nz_data+1] # branch-less increment
                nz_data = min(nz_data, zlevel_fractions.shape[1] - 2) # bound it to be one less than top cell

                # do vertical linear interp
                # get fraction within zlevel layer to use in interp
                dzf= abs(zlevel_fractions[node, nz_data + 1] - zlevel_fractions[node, nz_data])
                if dzf < .001:
                    f = 0.
                    dzf = 0.0
                else:
                    f = (sigma[nz] - zlevel_fractions[node, nz_data])/dzf

                # if in bottom data cell use log interp if water velocity
                # by adjusting f
                if nz_data == nz_bottom and is_water_velocity:
                    # get total water depth
                    twd = abs(tide[nt, node, 0, 0] + water_depth[0, node, 0, 0])
                    if twd < minimum_total_water_depth: twd = minimum_total_water_depth

                    # dz is  bottom layer thickness in metres, in original hydro model data
                    dz =  twd*dzf
                    if dz < z0:
                        f = 0.0
                    else:
                        z0p = z0 / dz
                        f = (np.log(f + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

                for m in range(out.shape[3]):
                    out[nt,node,nz,m] = (1-f) *data[nt,node,nz_data,m] + f *data[nt,node,nz_data+1,m]
        # do top value at sigma= 1
            for m in range(out.shape[3]):
                out[nt, node, -1, m] = data[nt, node, -1, m]

            pass

    return out

@njitOT
def convert_layer_field_to_levels_from_fixed_depth_fractions(data, sigma_layer, sigma):
    # convert values at depth at center of the cell to values on the boundaries between cells baed on fractional layer/boundary depthsz
    # used in FVCOM reader
    data_levels = np.full((data.shape[0],) + (data.shape[1],) + (sigma.shape[0],), 0., dtype=np.float32)

    for nt in range(data.shape[0]):
        for n in range(data.shape[1]):
            for nz in range(1, data.shape[2]):
                # linear interp levels not, first or last boundary
                data_levels[nt, n, nz] = kernal_linear_interp1D(sigma_layer[nz - 1], data[nt, n, nz - 1], sigma_layer[nz], data[nt, n, nz], sigma[nz])

            # extrapolate to top zlevel
            data_levels[nt, n, -1] = kernal_linear_interp1D(sigma_layer[-2], data[nt, n, -2], sigma_layer[-1], data[nt, n, -1], sigma[-1])

            # extrapolate to bottom zlevel
            data_levels[nt, n, 0] = kernal_linear_interp1D(sigma_layer[0], data[nt, n, 0], sigma_layer[1], data[nt, n, 1], sigma[0])

    return data_levels

@njitOT
def get_node_layer_field_values(data, node_to_tri_map, tri_per_node,cell_center_weights):
    # get nodal values from data in surrounding cells based in distance weighting
    # used in FVCOM reader

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



@njitOT
def convert_layer_field_to_levels_from_depth_fractions_at_each_node(data, zfraction_layer, zfraction_level):
    # convert values at depth at center of the cell to values on the boundaries between cells baed on fractional layer/boundary depths
    # used in FVCOM reader
    data_levels = np.full((data.shape[0], data.shape[1], zfraction_level.shape[1]), 0., dtype=np.float32)

    for nt in range(data.shape[0]):
        for n in range(data.shape[1]):
            for nz in range(1,data.shape[2]):
                # linear interp levels not, first or last boundary
                data_levels[nt, n, nz] = kernal_linear_interp1D(zfraction_layer[n, nz - 1], data[nt, n, nz - 1], zfraction_layer[n, nz], data[nt, n, nz], zfraction_level[n, nz])

            # extrapolate to top zlevel
            data_levels[nt, n, -1] = kernal_linear_interp1D(zfraction_layer[n, - 2], data[nt, n, -2], zfraction_layer[n, -1], data[nt, n, -1], zfraction_level[n, -1])

            # extrapolate to bottom zlevel
            data_levels[nt, n, 0] = kernal_linear_interp1D(zfraction_layer[n, 0], data[nt, n, 0], zfraction_layer[n, 1], data[nt, n, 1], zfraction_level[n, 0])

    return data_levels

@njitOT
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

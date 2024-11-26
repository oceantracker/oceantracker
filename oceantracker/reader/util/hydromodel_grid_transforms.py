import numpy as np
from numba import njit
from oceantracker.interpolator.util.interp_kernals import kernal_linear_interp1D
from copy import copy
from oceantracker.util.numba_util import njitOT
from oceantracker.util.triangle_utilities import split_quad_cells

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
    grid['triangles'] = quad_cells[sel, :]

    return grid['triangles']


@njitOT
def convert_zlevels_to_fractions(zlevels,bottom_cell_index,z0):
    # get zlevels (nodes, depths) as fraction of water depth
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
                if is_water_velocity and nz_data == nz_bottom:
                    # get total water depth
                    twd = max( abs(tide[nt, node, 0, 0] + water_depth[0, node, 0, 0]), minimum_total_water_depth)

                    # dz is  bottom layer thickness in meters, in original hydro model data
                    dz =  twd*dzf
                    if dz < z0:
                        f = 0.0
                    else:
                        z0p = z0 / dz
                        f = (np.log(f + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

                for m in range(out.shape[3]):
                    out[nt,node,nz,m] = (1-f) *data[nt,node,nz_data,m] + f * data[nt,node,nz_data+1,m]

        # do top value at sigma= 1
            for m in range(out.shape[3]):
                out[nt, node, -1, m] = data[nt, node, -1, m]

            pass

    return out

@njitOT
def convert_mid_layer_sigma_top_bot_layer_values(data, sigma_layer, sigma):
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
def convert_mid_layer_fixedZ_top_bot_layer_values(data_zlayer, z_layer, z, bottom_cell_index,water_depth):
    # convert values at depth at center of the cell to values on the boundaries between cells baed on fractional layer/boundary depthsz
    # used in FVCOM reader

    # interface values have one more level than mid_layer data
    data_z = np.full((data_zlayer.shape[0],data_zlayer.shape[1],data_zlayer.shape[2]+1), np.nan, dtype=np.float32)

    for nt in range(2,data_zlayer.shape[0]):
        for n in range(data_zlayer.shape[1]):
            pass
            for nz in range(bottom_cell_index[n]+1, data_zlayer.shape[2]-1):
                # linear interp levels not, first or last boundary from surronding mid-layer values
                data_z[nt, n, nz+1] = kernal_linear_interp1D(z_layer[nz], data_zlayer[nt,n, nz],
                                                    z_layer[nz+1], data_zlayer[nt,n, nz+1], z[nz+1])

            # make top level same as middle of top layer value, ie no shear
            data_z[nt, n, -1] = data_zlayer[nt, n, -1]

            # extrapolate to first z_interface above the bottom, ie top surface of bottom layer, if enough cells
            nz1 = bottom_cell_index[n]+1
            if nz1+1 < z_layer.size:
                data_z[nt, n, nz1] = kernal_linear_interp1D(z_layer[nz1], data_zlayer[nt, n, nz1],
                                                z_layer[nz1+1], data_zlayer[nt, n, nz1+1],
                                                        z[bottom_cell_index[n]])

            # make seabed values same as top of bottom layer
            data_z[nt, n, bottom_cell_index[n]] = data_z[nt, n, nz1]
                    # note - preprocessing will make water_velocity zero at seabed
            pass
        pass
    return data_z

@njitOT
def get_nodal_values_from_weighted_data(data, node_to_tri_map, tri_per_node, cell_center_weights):
    # get nodal values from 4D data in surrounding cells based in distance weighting
    # used in FVCOM, DELFT3D FM  reader
    #todo make this faster as works in 4D?
    s = (data.shape[0],len(node_to_tri_map)) + data.shape[2:4]
    data_nodes = np.full( s , 0., dtype=np.float32)

    for nt in range(data.shape[0]): # loop over time steps
        # loop over triangles
        for node in range(s[1]):
            for nz in range(s[2]):
                # loop over cells containing this node
                for m in range(tri_per_node[node]):
                    cell = node_to_tri_map[node, m]
                    data_nodes[nt, node, nz] += data[nt, cell, nz]*cell_center_weights[node, m] # weight this cell value

    return data_nodes

def get_node_to_cell_map(cell_nodes, n_nodes):
    # map nodes to the cells which connect to them
    # works with mix of triangular and quad cells
    # if 4th index < 0 then it is taken as a triangle, not quad

    # expanding output to allow any number of cells per node
    E =  np.full((n_nodes,5),-999,dtype=np.int32)
    node_to_cell_map= E.copy()
    cells_per_node = np.full((n_nodes, ), 0, dtype=np.int32)

    for n_cell, en in enumerate(cell_nodes):

        for m in range(cell_nodes.shape[1]):
            node = en[m]
            if node < 0 : break # if last one missing in mixed quad/tri cells

            node_to_cell_map[node,cells_per_node[node]] = n_cell
            cells_per_node[node] += 1

            # expand map if more column needed
            if cells_per_node[node] >= node_to_cell_map.shape[1]:
                 node_to_cell_map= np.concatenate((node_to_cell_map,E),axis=1)
    return node_to_cell_map, cells_per_node

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
def calculate_inv_dist_weights_at_node_locations(x_node, x_data, node_to_data_map, data_per_node):
    # calculate distance weights at nodes fot
    # for the values assocaite with the node as given in node_to_data_map
    weights= np.full_like(node_to_data_map, 0.,dtype=np.float32)
    dxy= np.full((2,), 0.,dtype=np.float32)

    for n in range(x_node.shape[0]):
        s= 0.
        n_data=data_per_node[n]
        for m in range(n_data):
            dxy[:] = x_data[node_to_data_map[n,m], :2] - x_node[n, :2]
            dist = np.sqrt(dxy[0]**2 + dxy[1]**2)
            dist= max(1.0e-2, dist) # no less than 1cm, ie value at node
            weights[n, m] = 1./dist
            s += weights[n, m]

        # normalize weights
        for m in range(n_data): weights[n,m]=weights[n,m] /s

    return weights



import numpy as np
from numba import njit
from numba.typed import List as NumbaList
from oceantracker.util.numba_util import  njitOT

@njitOT
def set_dry_cell_flag_from_z_interface( triangles, z_interface, bottom_interface_index, minimum_total_water_depth, is_dry_cell,buffer_index):
    #  flag cells dry if cell any node is dry
    for nb in buffer_index:
        for ntri in range(triangles.shape[0]):
            # count dry nodes
            n_dry = 0
            for m in triangles[ntri, :]:
                h = z_interface[nb,m, -1] - z_interface[nb,m, bottom_interface_index[m]]
                if h < minimum_total_water_depth: n_dry += 1
            is_dry_cell[nb, ntri] = 1 if n_dry > 0 else 0

@njitOT
def set_dry_cell_flag_from_tide(triangles, tide, depth, minimum_total_water_depth, is_dry_cell, buffer_index ):
    #  flag cells dry if cell any node is dry, seems to give closest to schism dry cells, rather than using > 1 or 2
    for nb in buffer_index:
        for ntri in range(triangles.shape[0]):
            # count dry nodes
            n_dry = 0
            for m in triangles[ntri,:]:
                h = tide[nb, m, 0 , 0] + depth[0, m, 0, 0]
                if h < minimum_total_water_depth : n_dry+=1
            is_dry_cell[nb, ntri] = 1 if n_dry > 0 else 0

@njitOT
def find_open_boundary_faces(triangles, is_boundary_triangle, adjacency, is_open_boundary_node):
    # amongst boundary triangles find those with 2 open face nodes
    is_open_boundary_adjacent = np.full((triangles.shape[0],3),False)
    is_open_node = np.full((3,),False)
    # search only boundary triangles
    op_nodes = np.flatnonzero(is_open_boundary_node)
    for n in np.flatnonzero(is_boundary_triangle==1):
        is_open_node[:] = False
        for m in range(3):
             for o in op_nodes:
               if o == triangles[n,m]:
                   # if next node is also open then tag face
                    is_open_node[m]= True
                    continue # stop looking

        if np.sum(is_open_node) <= 1:continue # only one open node

        # now know which of 3 nodes is open
        # now flag the open face if current and next node is an opend one
        for m in range(3):
            if is_open_node[m] and is_open_node[(m+1) % 3]:
                # open face number is node number opposite the two open face nodes
                is_open_boundary_adjacent[n, (m + 2) % 3] = True

    return is_open_boundary_adjacent



def append_split_cell_data(grid,data, axis=0):
    # for cell based data add split cell data below given data
    return  np.concatenate((data, data[:, grid['quad_cells_to_split']]), axis=axis)


@njitOT
def get_values_at_bottom(field_data4D, bottom_interface_index, out=None):
    # get values from bottom cell of LSC grid from a 3D time dependent field, (ie 4D with time)
    if out is None:
        s=field_data4D.shape
        out = np.full(s[:2]+(s[3],), np.nan,dtype=field_data4D.dtype)

    for n in range(field_data4D.shape[1]):
        out[:,n,:] = field_data4D[:, n, bottom_interface_index[n], :]
    return out


@njitOT
def depth_aver_SlayerLSC_in4D(field_data4D, z_interface, first_cell_offset):
    # depth average time varying reader 4D data dim(time, node, depth, components) and return for LSC vertical grid
    # return as 4D variable dim(time, node, 1, components)

    # set up with depth dim
    s = field_data4D.shape
    out = np.zeros((s[0], s[1], 1, min(s[3], 2)), dtype=field_data4D.dtype)

    for nt in range(out.shape[0]):  # time
        for n in range(out.shape[1]):  # loop over node

            n0 = first_cell_offset[n]
            h = z_interface[nt, n, -1] - z_interface[nt, n, n0]
            if h <= 0:
                out[nt, n, 0, :] = 0.0
                continue
            for m in range(out.shape[3]):  # loop over vector components
                d = 0.
                for nz in range(n0, field_data4D.shape[2] - 1):
                    d += 0.5 * (field_data4D[nt, n, nz, m] + field_data4D[nt, n, nz + 1, m]) * (z_interface[nt, n, nz + 1] - z_interface[nt, n, nz])
                out[nt, n, 0, m] = d / h
    return out


@njitOT
def get_time_dependent_triangle_water_depth_from_total_water_depth_at_nodes(total_water_depth_at_nodes, buffer_index, triangles, out):
    # get total time dependent water for grid triangles for use in calc like depth averaged concentrations
    # not used at the moment
    for nt in buffer_index:
        for m in range(triangles.shape[0]):
            out[nt, m] = 0.
            for v in range(3):
                out[nt,m] += total_water_depth_at_nodes[nt, triangles[m,v]] / 3.0  # todo use simple average, but better way?

@njitOT
def z_interface_node_to_vertex(z_interface, triangles, z_interface_vertex):
    # get z_interface at triangle vertices
    for nt in range(z_interface.shape[0]):
        for ntri in range(triangles.shape[0]):
            for nz in range(z_interface.shape[2]):
                for m in range(3):
                    z_interface_vertex[nt, ntri, nz, m] = z_interface[nt, triangles[ntri,m],  nz]


@njitOT
def ensure_velocity_at_bottom_is_zero_ragged_bottom(vel_data, bottom_interface_index):
    # ensure velocity vector at bottom is zero, as patch LSC vertical grid issue with nodal values spanning change in number of depth levels
    # needed in schsoim LSC grids due to interplotion bug
    for nt in range(vel_data.shape[0]):
        for node in range(vel_data.shape[1]):
            bottom_node= bottom_interface_index[node]
            for component in range(vel_data.shape[3]):
                vel_data[nt, node, bottom_node, component] = 0.


@njitOT
def get_values_at_ragged_bottom(data, bottom_interface_index):
    # from 4D field
    s = data.shape
    out = np.full(s[:2]+(s[3],), 0.,dtype=data.dtype)
    for nt in range(data.shape[0]):
        for node in range(data.shape[1]):
            bottom_node= bottom_interface_index[node]
            for component in range(data.shape[3]):
                out[nt, node, component] = data[nt, node, bottom_node, component]
    return out

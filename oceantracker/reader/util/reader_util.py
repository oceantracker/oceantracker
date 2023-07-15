import numpy as np
from numba import njit
from numba.typed import List as NumbaList

@njit()
def set_dry_cell_flag_from_zlevel( triangles, zlevel, bottom_cell_index, minimum_total_water_depth, is_dry_cell,buffer_index):
    #  flag cells dry if cell any node is dry
    for nb in buffer_index:
        for ntri in range(triangles.shape[0]):
            # count dry nodes
            n_dry = 0
            for m in triangles[ntri, :]:
                h = zlevel[nb,m, -1] - zlevel[nb,m, bottom_cell_index[m]]
                if h < minimum_total_water_depth: n_dry += 1
            is_dry_cell[nb, ntri] = 1 if n_dry > 0 else 0

@njit()
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

@njit
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



def append_split_cell_data(grid,data,axis=0):
    # for cell based data add split cell data below given data
    return  np.concatenate((data, data[:, grid['quad_cells_to_split']]), axis=axis)


@njit()
def get_values_at_bottom(field_data4D, bottom_cell_index, out=None):
    # get values from bottom cell of LSC grid from a 3D time dependent field, (ie 4D with time)
    if out is None:
        s=field_data4D.shape
        out = np.full(s[:2]+(s[3],), np.nan,dtype=field_data4D.dtype)

    for n in range(field_data4D.shape[1]):
        out[:,n,:] = field_data4D[:, :, bottom_cell_index[n], :]
    return out


@njit
def depth_aver_SlayerLSC_in4D(field_data4D, zlevel, first_cell_offset):
    # depth average time varying reader 4D data dim(time, node, depth, components) and return for LSC vertical grid
    # return as 4D variable dim(time, node, 1, components)

    # set up with depth dim
    s = field_data4D.shape
    out = np.zeros((s[0], s[1], 1, min(s[3], 2)), dtype=field_data4D.dtype)

    for nt in range(out.shape[0]):  # time
        for n in range(out.shape[1]):  # loop over node

            n0 = first_cell_offset[n]
            h = zlevel[nt, n, -1] - zlevel[nt, n, n0]
            if h <= 0:
                out[nt, n, 0, :] = 0.0
                continue
            for m in range(out.shape[3]):  # loop over vector components
                d = 0.
                for nz in range(n0, field_data4D.shape[2] - 1):
                    d += 0.5 * (field_data4D[nt, n, nz, m] + field_data4D[nt, n, nz + 1, m]) * (zlevel[nt, n, nz + 1] - zlevel[nt, n, nz])
                out[nt, n, 0, m] = d / h
    return out


@njit()
def get_time_dependent_triangle_water_depth_from_total_water_depth_at_nodes(total_water_depth_at_nodes, buffer_index, triangles, out):
    # get total time dependent water for grid triangles for use in calc like depth averaged concentrations
    # not used at the moment
    for nt in buffer_index:
        for m in range(triangles.shape[0]):
            out[nt, m] = 0.
            for v in range(3):
                out[nt,m] += total_water_depth_at_nodes[nt, triangles[m,v]] / 3.0  # todo use simple average, but better way?

@njit()
def zlevel_node_to_vertex(zlevel, triangles, zlevel_vertex):
    # get zlevel at triangle vertices
    for nt in range(zlevel.shape[0]):
        for ntri in range(triangles.shape[0]):
            for nz in range(zlevel.shape[2]):
                for m in range(3):
                    zlevel_vertex[nt, ntri, nz, m] = zlevel[nt, triangles[ntri,m],  nz]


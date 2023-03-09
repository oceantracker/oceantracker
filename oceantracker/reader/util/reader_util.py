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
    for n in np.flatnonzero(is_boundary_triangle):
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

def split_quad_cells(triangles_and_quads,quad_cells_to_split):
    # find indices flagged by boolean for splitting
    # put split cell info next to each other which mayu speed accesing getting nodal data from memory due to caching
    if quad_cells_to_split is not None:
        num_tri_quad=triangles_and_quads.shape[0]
        num_to_split = np.sum(quad_cells_to_split)
        triangles = np.full((num_tri_quad+num_to_split, 3),-1,dtype=np.int32)
        triangles[:num_tri_quad,:] = triangles_and_quads[: ,:3] # those not split

        qtri = triangles_and_quads[quad_cells_to_split, :]# simplex for those to split
        triangles[num_tri_quad:, :] = qtri[:, [0, 2, 3]]
    return triangles

def append_split_cell_data(grid,data,axis=0):
    # for cell based data add split cell data below given data
    return  np.concatenate((data, data[:, grid['quad_cells_to_split']]), axis=axis)
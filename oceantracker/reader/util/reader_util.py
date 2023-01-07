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


@njit()
def convert_numpy_node_to_tri_map_to_numba_list(node_to_tri_map_asarray):
    # convert a rectangular map to a  list of lists, missing values are -99999
    node_to_tri_map= NumbaList()

    for l in node_to_tri_map_asarray:
        node_to_tri_map.append(list(l[l >= 0]))

    return node_to_tri_map
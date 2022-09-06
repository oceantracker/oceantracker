from numba import njit


@njit()
def set_dry_cell_flag_from_zlevel(buffer_index, triangles, zlevel, bottom_cell_index, minimum_total_water_depth, is_dry_cell):
    #  flag cells dry if total water depth of any node is dry, ie less than min water depth
    for nb in buffer_index:
        for ntri in range(triangles.shape[0]):
            is_dry_cell[nb, ntri] = 0  # default is wet cell

            for n in range(triangles.shape[1]):
                node = triangles[ntri,n]
                if zlevel[nb,node, -1] - zlevel[nb,node, bottom_cell_index[node]] < minimum_total_water_depth:
                   is_dry_cell[nb, ntri] = 1
                   break  # dry if any node is dry, so stop looking

@njit()
def set_dry_cell_flag_from_tide(buffer_index, triangles, tide, depth, minimum_total_water_depth, is_dry_cell):
    #  flag cells dry if total water depth of any node is dry, ie less than min water depth
    for nb in buffer_index:
        for ntri in range(triangles.shape[0]):
            is_dry_cell[nb, ntri] = 0  # default is wet cell

            for n in range(triangles.shape[1]):
                node = triangles[ntri,n]
                if tide[nb, node,0, 0] + depth[0,node, 0, 0] < minimum_total_water_depth:
                   is_dry_cell[nb, ntri] = 1
                   break  # dry if any node is dry, so stop looking
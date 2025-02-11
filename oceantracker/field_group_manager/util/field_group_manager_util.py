from oceantracker.util.numba_util import njitOT
from oceantracker.definitions import cell_search_status_flags
dry_cell_edge = int(cell_search_status_flags.dry_cell_edge)


@njitOT
def update_dry_cell_index(is_dry_cell_buffer, dry_cell_index, current_buffer_steps, fractional_time_steps):
    # update 0-255 dry cell index, used to determine if cell dry at this time
    # uses  reader buffer locations and time step fractions within step info structure
    # vals > 127 are dry, vals <= 127 are wet
    for n in range(dry_cell_index.size):
        val = fractional_time_steps[0] * is_dry_cell_buffer[current_buffer_steps[0], n]
        val += fractional_time_steps[1] * is_dry_cell_buffer[current_buffer_steps[1], n]
        dry_cell_index[n] = int(255. * val)

@njitOT
def update_dry_cell_adjacency(adjacency, dry_cell_index, adjacency_with_dry_cells):
    # add dry cell lateral boundaries to adjacency for use in triangle walk
    for n in range(adjacency_with_dry_cells.shape[0]):
        for m in range(3):
            adjacency_with_dry_cells[n, m] = adjacency[n, m]  # copy over adjacency with domain and open boundaries

            if adjacency[n, m] >= 0 and dry_cell_index[adjacency[n, m]] > 128:
                # make face a dry cell boundary if adjacent cell is dry
                # but leave  domain and open boundary adjacencies
                adjacency_with_dry_cells[n, m] = dry_cell_edge

            pass

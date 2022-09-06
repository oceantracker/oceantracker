from numba import njit

@njit
def update_dry_cell_index(nb ,time_step_fraction, dry_cells, dry_cell_index):
    # make 0-255 index of how dry cells are
    tf2= 1.0 - time_step_fraction
    for n in range(dry_cell_index.shape[0]):
            dry_cell_index[n]= int(255.*(tf2*float(dry_cells[nb,n]) + time_step_fraction*float(dry_cells[nb+1, n])))
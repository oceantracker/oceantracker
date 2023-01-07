from numba import njit
import numpy as np
@njit
def update_dry_cell_index(nb ,time_step_fraction, dry_cells, dry_cell_index):
    # make 0-255 index of how dry cells are
    tf2= 1.0 - time_step_fraction
    for n in range(dry_cell_index.shape[0]):

        dry_cell_index[n]= int(255.*(tf2*float(dry_cells[nb,n]) + time_step_fraction*float(dry_cells[nb+1, n])))

        #if dry_cells[nb, n] != dry_cells[nb + 1, n] and time_step_fraction!=0. and time_step_fraction!=1.:
        #    print('xxx', dry_cells[nb, n], dry_cells[nb + 1, n],dry_cell_index[n],time_step_fraction)
        #    pass
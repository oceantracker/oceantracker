from scipy.spatial import cKDTree
import numpy as np

from oceantracker.shared_info import shared_info as si
from time import perf_counter
from oceantracker.util import numpy_util
from oceantracker.interpolator.util import triangle_interpolator_util,  find_initial_cell

from oceantracker.util.numba_util import  njitOT, njitOTparallel
import numba as nb
# globals

# globals to compile into numba to save pass arguments
# numba code needs integer versions of constants
psf = si.particle_status_flags

status_moving = int(psf.moving)
status_on_bottom = int(psf.on_bottom)
status_stranded_by_tide = int(psf.stranded_by_tide)
status_outside_domain = int(psf.outside_domain)
status_outside_open_boundary = int(psf.outside_open_boundary)
status_dead = int(psf.dead)
status_bad_coord = int(psf.bad_coord)
status_cell_search_failed = int(psf.cell_search_failed)
status_hit_dry_cell = int(psf.hit_dry_cell)


domain_edge =  int(si.edge_types.domain)
open_bounday_edge=  int(si.edge_types.open_boundary)


class FindHoriCellTriangleWalk(object):

    def __init__(self, grid, params):

        self.grid, self.params= grid, params
        self.info={}

        # tree for initial serach
        self.KDtree = cKDTree(grid['x'])

        # pre calc matric to calculate bc coords
        t0= perf_counter()
        grid['bc_transform'] = triangle_interpolator_util.get_BC_transform_matrix(grid['x'].data, grid['triangles'].data).astype(np.float64)

        # build triangle walk array of structures
        self.tri_walk_AOS = numpy_util.numpy_array_of_structures_from_dict(
            dict(bc_transform= grid['bc_transform'],
                 adjacency=grid['adjacency'],
                 #   adjacency=grid['adjacency_with_dry_edges']
                 )
        )
        si.msg_logger.progress_marker('built barycentric-transform matrix', start_time=t0,tabs=2)

        # classes need by this class
        crumbs = 'interpolator intitial_setup>'
        si.add_class('particle_properties', name='n_cell', class_name='ManuallyUpdatedParticleProperty', write=False, dtype='int32',
                     initial_value=0, caller=self, crumbs=crumbs)  # start with cell number guess of zero
        si.add_class('particle_properties', name='n_cell_last_good', class_name='ManuallyUpdatedParticleProperty', write=False, dtype='int32',
                     initial_value=0, caller=self, crumbs=crumbs)
        si.add_class('particle_properties', name='need_fixingIDs', class_name='ManuallyUpdatedParticleProperty',
                     write=False, dtype='int32',
                     initial_value=0, caller=self, crumbs=crumbs)
        si.add_class('particle_properties', name='bc_coords', class_name='ManuallyUpdatedParticleProperty', write=False,
                     initial_value=0., vector_dim=3, dtype='float32', caller=self, crumbs=crumbs)
        si.add_class('particle_properties', name='bc_coords_last_good', class_name='ManuallyUpdatedParticleProperty', write=False,
                     initial_value=0., vector_dim=3, dtype='float32', caller=self, crumbs=crumbs)

        self.walk_counts = np.zeros((6,), dtype=np.int64)
        wc = self.walk_counts
        self.info.update(particles_located_by_walking=wc[0:1],
                         number_of_triangles_walked=wc[1:2],
                         longest_triangle_walk=wc[2:3],
                         nans_encountered_triangle_walk=wc[3:4],
                         triangle_walks_retried=wc[4:5],
                         particles_killed_after_triangle_walk_retry_failed=wc[5:6],
                    )
    def find_initial_cell(self, xq):
        # find nearest cell to xq
        t0 = perf_counter()
        n_cell, bc, is_inside_domain= find_initial_cell.find_cellKDtree(xq, self.grid, self.KDtree, self.params['bc_walk_tol'])
        si.block_timer('Initial cell guess', t0)
        return n_cell, bc, is_inside_domain


    def find_cell(self,xq, active):
        part_prop = si.class_roles.particle_properties
        grid= self.grid
        n_cell = part_prop['n_cell'].data
        bc_coords = part_prop['bc_coords'].data
        status = part_prop['status'].data
        need_fixingIDs = part_prop['need_fixingIDs'].data
        params = self.params

        IDs_need_fixing= self.BCwalk(xq,
                                self.tri_walk_AOS, grid['dry_cell_index'],
                                n_cell, status, need_fixingIDs ,bc_coords,
                                self.walk_counts,
                                params['max_search_steps'], params['bc_walk_tol'],
                                si.settings['block_dry_cells'], active)
        return IDs_need_fixing

    def close(self):
        info= self.info
        # convert mapped array counts to int
        for key in info.keys():
            if isinstance(info[key], np.ndarray) and info[key].size == 1:
                info[key] = int(info[key])

    @staticmethod
    @njitOTparallel
    def BCwalk(xq, tri_walk_AOS, dry_cell_index,
               n_cell, status, need_fixingIDs, bc_coords,
               walk_counts,
               max_triangle_walk_steps, bc_walk_tol, block_dry_cells,
               active):
        # Barycentric walk across triangles to find cells

        thread_buffer_index = [nb.typed.List.empty_list(nb.types.int32) for n in range(nb.get_num_threads())]

        # loop over active particles in place
        for nn in nb.prange(active.size):
            n = active[nn]
            bc = bc_coords[n, :]

            if np.isnan(xq[n, 0]) or np.isnan(xq[n, 1]):
                # if any is nan copy all and move on
                status[n] = status_bad_coord
                thread_buffer_index[nb.get_thread_id()].append(n)
                continue

            n_tri = n_cell[n]  # starting triangle
            # do BC walk
            n_steps = 0
            cell_search_OK = True

            while n_steps < max_triangle_walk_steps:
                # update barcentric cords of xq

                n_min, n_max = triangle_interpolator_util._get_single_BC_cord_numba(xq[n, :], tri_walk_AOS[n_tri]['bc_transform'], bc)

                if bc[n_min] > -bc_walk_tol and bc[n_max] < 1. + bc_walk_tol:
                    # are now inside triangle, leave particle status as is
                    break  # with current n_tri as found cell

                n_steps += 1
                # move to neighbour triangle at face with smallest bc then test bc cord again
                next_tri = tri_walk_AOS[n_tri]['adjacency'][n_min]  # n_min is the face num in  tri to move across

                if next_tri < 0:
                    # if no new adjacent triangle, then are trying to exit domain at a boundary triangle,
                    # keep n_cell, bc  unchanged
                    if next_tri == open_bounday_edge:  # outside domain
                        # leave x, bc, cell, location  unchanged as outside
                        status[n] = status_outside_open_boundary
                        cell_search_OK = False
                        break
                    else:  # n_tri == -1 outside domain and any future
                        # solid boundary, so just move back
                        status[n] = status_outside_domain
                        cell_search_OK = False
                        break

                # check for dry cell
                if block_dry_cells:  # is faster split into 2 ifs, not sure why
                    if dry_cell_index[next_tri] > 128:
                        # treats dry cell like a lateral boundary,  move back and keep triangle the same
                        status[n] = status_hit_dry_cell
                        cell_search_OK = False
                        break

                n_tri = next_tri

            # not found in given number of search steps
            if n_steps >= max_triangle_walk_steps:  # dont update cell
                status[n] = status_cell_search_failed
                cell_search_OK = False

            if cell_search_OK:
                # update cell anc BC for new triangle, if not fixed in solver after full step
                n_cell[n] = n_tri
            else:
                # record ID to fix outside
                thread_buffer_index[nb.get_thread_id()].append(n)

            # walk_counts[1] += n_steps  # steps taken
            # walk_counts[2] = max(n_steps,  walk_counts[2])  # longest walk

        walk_counts[0] += active.size  # particles walked

        # merge index IDs for those needing fixing from each thread
        n_found = 0
        for IDs in thread_buffer_index:
            for ID in IDs:
                need_fixingIDs[n_found] = ID
                n_found += 1

        return need_fixingIDs[:n_found]  # return IDs of those needing fixing
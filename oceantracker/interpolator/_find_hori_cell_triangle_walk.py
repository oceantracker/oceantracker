from scipy.spatial import cKDTree
import numpy as np

from oceantracker.shared_info import shared_info as si
from oceantracker.definitions import cell_search_status_flags

from oceantracker.interpolator._base_interp import _BaseInterp
from oceantracker.util import basic_util
from oceantracker.util.profiling_util import function_profiler
from time import perf_counter
from oceantracker.util import numpy_util
from oceantracker.interpolator.util import triangle_interpolator_util as tri_interp_util ,  triangle_eval_interp
from oceantracker.particle_properties.util import  particle_operations_util

class FindHoriCellTriangleWalk(object):

    def __init__(self, grid, params):

        self.grid, self.params= grid, params
        self.info={}

        # tree for initial serach
        self.KDtree = cKDTree(grid['x'])

        # pre calc matric to calculate bc coords
        t0= perf_counter()
        self.bc_transform = tri_interp_util.get_BC_transform_matrix(grid['x'].data, grid['triangles'].data).astype(np.float64)

        # build triangle walk array of structures
        self.tri_walk_AOS = numpy_util.numpy_array_of_structures_from_dict(
            dict(bc_transform=self.bc_transform,
                 adjacency=grid['adjacency'],
                 #   adjacency=grid['adjacency_with_dry_edges']
                 )
        )
        # explore array of structures is faster?
        #self.tri_data =numpy_util.numpy_array_of_structures_from_dict(
        #                dict(triangles=grid['triangles'], adjacency=grid['adjacency'], bc_transform=self.bc_transform,
        #                                    ))

        si.msg_logger.progress_marker('built barycentric-transform matrix', start_time=t0)

        # classes need by this class
        crumbs = 'interpolator intitial_setup>'
        si.add_class('particle_properties', name='n_cell', class_name='ManuallyUpdatedParticleProperty', write=False, dtype='int32',
                     initial_value=0, caller=self, crumbs=crumbs)  # start with cell number guess of zero
        si.add_class('particle_properties', name='n_cell_last_good', class_name='ManuallyUpdatedParticleProperty', write=False, dtype='int32',
                     initial_value=0, caller=self, crumbs=crumbs)
        si.add_class('particle_properties', name='cell_search_status', class_name='ManuallyUpdatedParticleProperty', write=False,
                     initial_value=cell_search_status_flags.ok, dtype='int8', caller=self, crumbs=crumbs)
        si.add_class('particle_properties', name='bc_cords', class_name='ManuallyUpdatedParticleProperty', write=False,
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
        grid= self.grid
        t0 = perf_counter()

        # find nearest node
        dist, nodes = self.KDtree.query(xq[:, :2])
        nodes = nodes.astype(np.int32)  # KD tree gives int64,need for compatibility of types

        # look in triangles attached to each node for tri containing the point
        # t0= perf_counter()
        is_inside_domain, n_cell, bc  = tri_interp_util.check_if_point_inside_triangle_connected_to_node(xq[:, :2], nodes,
                                    grid['node_to_tri_map'], grid['tri_per_node'],
                                    self.bc_transform, self.params['bc_walk_tol'])
        # if x is nan dist is infinite
        n_cell[~np.isfinite(dist)] = -1
        si.block_timer('Initial cell guess', t0)
        return n_cell, bc, is_inside_domain

    def find_cell(self,xq, active):
        part_prop = si.class_roles.particle_properties
        grid= self.grid
        n_cell = part_prop['n_cell'].data
        bc_cords = part_prop['bc_cords'].data
        cell_search_status = part_prop['cell_search_status'].data
        params = self.params

        tri_interp_util.BCwalk(xq,
            self.tri_walk_AOS, grid['dry_cell_index'],
            n_cell, cell_search_status, bc_cords,
            self.walk_counts,
            params['max_search_steps'], params['bc_walk_tol'],
            si.settings.open_boundary_type, si.settings['block_dry_cells'], active)

    def close(self):
        info= self.info
        # convert mapped array counts to int
        for key in info.keys():
            if isinstance(info[key], np.ndarray) and info[key].size == 1:
                info[key] = int(info[key])
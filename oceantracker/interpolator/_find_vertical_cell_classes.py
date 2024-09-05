from scipy.spatial import cKDTree
import numpy as np

from oceantracker.shared_info import shared_info as si
from oceantracker.util import basic_util
from oceantracker.util.profiling_util import function_profiler
from time import perf_counter
from oceantracker.util import numpy_util
from oceantracker.interpolator.util import  triangle_eval_interp
from oceantracker.particle_properties.util import  particle_operations_util
from oceantracker.util.numba_util import njitOT

# globals to complile into numba to save pass arguments
psf = si.particle_status_flags
status_moving = int(psf['moving'])
status_on_bottom = int(psf['on_bottom'])
status_stranded_by_tide = int(psf['stranded_by_tide'])
status_outside_open_boundary = int(psf['outside_open_boundary'])
status_dead = int(psf['dead'])
status_bad_cord = int(psf['bad_cord'])
status_cell_search_failed = int(psf['cell_search_failed'])

class FindVerticalCellSigmaGrid(object):

    def __init__(self, grid, params):
        self.grid, self.params = grid, params
        self.info = {}
        self._make_sigma_depth_cell_search_map(grid)
        pass
    def _make_sigma_depth_cell_search_map(self, grid):
        # add lookup map to grid
        # setup lookup nz interval map of zfraction into with equal dz for finding vertical cell
        # the smalest sigms later thickness is at the bottom

        grid['sigma_nz_map'], grid['sigma_map_dz'] = make_search_map(grid['sigma'])



    def find_vertical_cell(self, fields, xq, current_buffer_steps, fractional_time_steps, active):
        # locate vertical cell in place
        part_prop = si.class_roles.particle_properties
        n_cell = part_prop['n_cell_last_good'].data
        status = part_prop['status'].data
        bc_cords = part_prop['bc_cords'].data
        grid = self.grid

        nz_cell = part_prop['nz_cell'].data
        z_fraction = part_prop['z_fraction'].data
        z_fraction_water_velocity = part_prop['z_fraction_water_velocity'].data

        self.get_depth_cell_sigma_layers(xq,
                                    grid['triangles'],
                                    fields['water_depth'].data.ravel(),
                                    fields['tide'].data,
                                    si.settings.minimum_total_water_depth,
                                    grid['sigma'], grid['sigma_nz_map'], grid['sigma_map_dz'],
                                    n_cell, status, bc_cords, nz_cell, z_fraction, z_fraction_water_velocity,
                                    current_buffer_steps, fractional_time_steps,
                                    active, si.settings.z0)

    @staticmethod
    @njitOT
    def get_depth_cell_sigma_layers(xq, triangles, water_depth, tide, minimum_total_water_depth,
                                    sigma, sigma_map_nz,sigma_map_dz,
                                    n_cell, status, bc_cords, nz_cell, z_fraction, z_fraction_water_velocity,
                                    current_buffer_steps, fractional_time_steps,
                                    active, z0):
        # temp working space for interp eval

        for n in active:  # loop over active particles
            nodes = triangles[n_cell[n], :]  # nodes for the particle's cell
            zq = float(xq[n, 2])

            # interp water depth
            # z_bot = _eval_water_depth_kernel(water_depth,bc_cords[n,:], nodes)
            z_bot = 0.
            for m in range(3):
                z_bot -= bc_cords[n, m] * water_depth[nodes[m]]

            # preserve status if stranded by tide
            if status[n] == status_stranded_by_tide:
                nz_cell[n] = 0
                xq[n, 2] = z_bot
                z_fraction[n] = 0.0
                z_fraction_water_velocity[n] = 0.0
                continue

            # interp tide
            z_top = 0.
            for m in range(3):
                z_top += bc_cords[n, m] * tide[current_buffer_steps[0], nodes[m], 0, 0] * fractional_time_steps[0]
                z_top += bc_cords[n, m] * tide[current_buffer_steps[1], nodes[m], 0, 0] * fractional_time_steps[1]

            # clip z into range
            zq = min(max(zq, z_bot), z_top)

            twd = max(abs(z_top - z_bot), minimum_total_water_depth)
            zf = max(0., min(abs(zq - z_bot) / twd, 0.9999))  # with rounding keep, it just below surface, and at or above bottom

            # get  nz from evenly space sigma map, but zf always < 1, due to above
            ns = int(zf/sigma_map_dz)  # find fraction of length of map index

            # get approx nz from map
            nz = sigma_map_nz[ns]

            # correction
            # sigma_map_nz rounds down, so correct if zf is below sigma[nz]  by subtracting 1, as nz  is 1 above approx nz
            nz -= zf > sigma[nz]  # faster branch-less add one

            # get fraction within the sigma layer
            z_fraction[n] = (zf - sigma[nz]) / (sigma[nz + 1] - sigma[nz])

            # make any already on bottom active, may be flagged on bottom if found on bottom, below
            if status[n] == status_on_bottom:
                status[n] = status_moving

            # extra work if in bottom cell
            z_fraction_water_velocity[n] = z_fraction[n]
            if nz == 0:
                z0f = z0 / twd  # z0 as fraction of water depth
                # set status if on the bottom set status
                if zf < z0f:
                    status[n] = status_on_bottom
                    zq = z_bot
                    z_fraction_water_velocity[n] = 0.0
                else:
                    # adjust z fraction so that linear interp acts like log layer
                    z1 = (sigma[1] - sigma[0]) * twd  # dimensional bottom layer thickness
                    z0p = z0 / z1
                    z_fraction_water_velocity[n] = (np.log(z_fraction[n] + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

            # record new depth cell
            nz_cell[n] = nz
            xq[n, 2] = zq

        pass

class FindVerticalCellSlayerLSCGrid(object):

    def __init__(self, grid, params):
        self.grid, self.params = grid, params
        self.info = {}
        self.walk_counts= np.zeros((2,), dtype=np.int64)

    def find_vertical_cell(self, fields, xq, current_buffer_steps, fractional_time_steps, active):
        part_prop = si.class_roles.particle_properties
        n_cell = part_prop['n_cell_last_good'].data
        status = part_prop['status'].data
        bc_cords = part_prop['bc_cords'].data
        grid = self.grid

        nz_cell = part_prop['nz_cell'].data
        z_fraction = part_prop['z_fraction'].data
        z_fraction_water_velocity = part_prop['z_fraction_water_velocity'].data

        self.get_depth_cell_time_varying_Slayer_or_LSCgrid(xq,grid['triangles'], grid['zlevel'], grid['bottom_cell_index'],
                                                      n_cell, status, bc_cords, nz_cell, z_fraction, z_fraction_water_velocity,
                                                      current_buffer_steps, fractional_time_steps,
                                                      self.walk_counts,
                                                      active, si.settings.z0)


    @staticmethod
    @njitOT
    def get_depth_cell_time_varying_Slayer_or_LSCgrid(xq,
                                                      triangles, zlevel, bottom_cell_index,
                                                      n_cell, status, bc_cords, nz_cell, z_fraction, z_fraction_water_velocity,
                                                      current_buffer_steps, fractional_time_steps,
                                                      walk_counts,
                                                      active, z0):
        # find the zlayer for each node of cell containing each particle and at two time slices of hindcast  between nz_bottom and number of z levels
        # LSC grid means must track vertical nodes for each particle
        # nz_with_bottom is the lowest cell in grid, is 0 for slayer vertical grids, but may be > 0 for LSC grids
        # nz_with_bottom must be time independent
        # vertical walk to search for a particle's layer in the grid, nz_cell

        def _eval_z_at_nz_cell(tf,nz_cell, zlevel1, zlevel2, nodes, nz_bottom_nodes, nz_top_cell, BCcord):
            # eval zlevel at particle location and depth cell, return z and nodes required for evaluation
            z = 0.
            for m in range(3):
                nz = max(min(nz_cell, nz_top_cell + 1), nz_bottom_nodes[m])  # move up to bottom, so not out of range
                z += BCcord[m] * (zlevel1[nodes[m], nz] * tf[1] + zlevel2[nodes[m], nz] * tf[0])
            return z

        nz_top_cell = zlevel.shape[2] - 2
        zl1 = zlevel[current_buffer_steps[0], ...]
        zl2 = zlevel[current_buffer_steps[1], ...]

        bottom_nz_nodes = np.zeros((3,), dtype=np.int32)
        for nn in range(active.size):  # loop over active particles
            n = active[nn]
            bc = bc_cords[n, :]

            nodes = triangles[n_cell[n], :]  # nodes for the particle's cell

            deepest_bottom_cell = nz_top_cell
            for m in range(3):
                bottom_nz_nodes[m] = bottom_cell_index[nodes[m]]
                deepest_bottom_cell = min(bottom_nz_nodes[m], deepest_bottom_cell)

            # preserve status if stranded by tide
            if status[n] == status_stranded_by_tide:
                nz_cell[n] = deepest_bottom_cell
                # update nodes above and below
                z_below = _eval_z_at_nz_cell(fractional_time_steps, deepest_bottom_cell, zl1, zl2, nodes, bottom_nz_nodes, nz_top_cell, bc)
                xq[n, 2] = z_below
                z_fraction[n] = 0.0
                continue

            n_vertical_steps = 0
            zq = xq[n, 2]

            # make any already on bottom active, may be flagged on bottom if found on bottom, below
            if status[n] == status_on_bottom: status[n] = status_moving

            # find zlevel above and below  current vertical cell
            nz = nz_cell[n]
            z_below = _eval_z_at_nz_cell(fractional_time_steps, nz, zl1, zl2, nodes, bottom_nz_nodes, nz_top_cell, bc)

            if zq >= z_below:
                # search upwards, do nothing if z_above > zq[n] > z_below, ie current nodes are correct
                z_above = _eval_z_at_nz_cell(fractional_time_steps, nz + 1, zl1, zl2, nodes, bottom_nz_nodes, nz_top_cell, bc)

                while zq > z_above and nz < nz_top_cell:
                    nz += 1
                    n_vertical_steps += 1
                    z_below = z_above
                    z_above = _eval_z_at_nz_cell(fractional_time_steps, nz + 1, zl1, zl2, nodes, bottom_nz_nodes, nz_top_cell, bc)
                # clip to free surface height
                if zq > z_above:
                    zq = z_above
                    nz = nz_top_cell
            else:
                # search downwards, move down one step
                nz = max(nz - 1, deepest_bottom_cell)  # take one step down to start
                n_vertical_steps += 1
                z_above = z_below
                z_below = _eval_z_at_nz_cell(fractional_time_steps, nz, zl1, zl2, nodes, bottom_nz_nodes, nz_top_cell, bc)

                while zq < z_below and nz > deepest_bottom_cell:
                    nz -= 1
                    n_vertical_steps += 1
                    z_above = z_below  # retain for dz calc.
                    z_below = _eval_z_at_nz_cell(fractional_time_steps, nz, zl1, zl2, nodes, bottom_nz_nodes, nz_top_cell, bc)

                # clip to bottom
                if zq < z_below:
                    zq = z_below
                    nz = deepest_bottom_cell

            # nz now holds required cell
            dz = z_above - z_below
            # get z linear z_fraction
            if dz < z0:
                z_fraction[n] = 0.0
            else:
                z_fraction[n] = (zq - z_below) / dz

            # extra work if in bottom cell
            z_fraction_water_velocity[n] = z_fraction[n]  # flag as not in bottom layer, will become >= 0 if in layer
            if nz == deepest_bottom_cell:
                # set status if on the bottom set status
                if zq < z_below + z0:
                    status[n] = status_on_bottom
                    zq = z_below

                # get z_fraction for log layer
                if dz < z0:
                    z_fraction_water_velocity[n] = 0.0
                else:
                    # adjust z fraction so that linear interp acts like log layer
                    z0p = z0 / dz
                    z_fraction_water_velocity[n] = (np.log(z_fraction[n] + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

            # record new depth cell
            nz_cell[n] = nz
            xq[n, 2] = zq
            # step count stats, tidal stranded particles are not counted
            walk_counts[0] += n_vertical_steps
            walk_counts[1] = max(walk_counts[1], n_vertical_steps)  # record max number of steps

class FindVerticalCellZfixed(object):
    # find depth cell with fized z levels everywhere with differing layer thickness's
    def __init__(self, grid, params):
        self.grid, self.params = grid, params
        self.info = {}

        # set up a Zmap
        self._make_fixedZ_cell_search_map(grid)


        pass
    def _make_fixedZ_cell_search_map(self, grid):
        # add lookup map to grid
        # setup lookup nz interval map of fixed z into with equal dz for finding vertical cell
        grid = self.grid
        #  dz for map layer thickness is smaller than smallest hydromodel dz
        grid['nz_map'], grid['dz_map'] = make_search_map(grid['z'])


    def find_vertical_cell(self, fields, xq, current_buffer_steps, fractional_time_steps, active):
        part_prop = si.class_roles.particle_properties
        n_cell = part_prop['n_cell_last_good'].data
        status = part_prop['status'].data
        bc_cords = part_prop['bc_cords'].data
        grid = self.grid

        nz_cell = part_prop['nz_cell'].data
        z_fraction = part_prop['z_fraction'].data
        z_fraction_water_velocity = part_prop['z_fraction_water_velocity'].data

        self.get_depth_cell_fixedZ(xq, grid['triangles'], grid['bottom_cell_index'],
                             grid['water_depth'], fields['tide'].data, grid['z'], grid['nz_map'], grid['dz_map'],
                             n_cell, status, bc_cords, nz_cell, z_fraction, z_fraction_water_velocity,
                             current_buffer_steps, fractional_time_steps,
                             active, si.settings.z0)
    @staticmethod
    @njitOT
    def get_depth_cell_fixedZ(xq, triangles, bottom_cell_index,water_depth,tide,
                                    z, nz_map,dz_map,
                                    n_cell, status, bc_cords, nz_cell, z_fraction, z_fraction_water_velocity,
                                    current_buffer_steps, fractional_time_steps,
                                    active, z0):

        for n in active:  # loop over active particles
            nodes = triangles[n_cell[n], :]  # nodes for the particle's cell
            zq = float(xq[n, 2])

            # interp to find water depth at particle location
            z_bot = 0.
            deepest_bottom_cell= nz_map[-1]
            for m in range(3):
                z_bot -= bc_cords[n, m] * water_depth[nodes[m]]
                # for ragged bottom, get the deepest cell
                # a particle could be amonst the 3 nodes
                deepest_bottom_cell = min(bottom_cell_index[nodes[m]],deepest_bottom_cell)

            # preserve status if stranded by tide
            if status[n] == status_stranded_by_tide:
                nz_cell[n] = deepest_bottom_cell
                xq[n, 2] = z_bot
                z_fraction[n] = 0.0
                z_fraction_water_velocity[n] = 0.0
                continue

            # interp to find tide at particle location
            z_top = 0.
            for m in range(3):
                z_top += bc_cords[n, m] * tide[current_buffer_steps[0], nodes[m], 0, 0] * fractional_time_steps[0]
                z_top += bc_cords[n, m] * tide[current_buffer_steps[1], nodes[m], 0, 0] * fractional_time_steps[1]

            zq = min(max(zq, z_bot), z_top) # clip to water depth and free surface
            n_in_map = int((zq - z[0]) / dz_map) # number of map steps between zq and deepest fixed z in the map

            # todo cleaner way to do below?
            n_in_map = min(n_in_map,nz_map.size-1) # clip inside map
            nz = nz_map[n_in_map]

            #print('xx', nz, zq, z_top, z[-3:])

            if nz == z.size-2: # in top layer
                # treat top layer as variable in thickness, bewteen tide and next interface
                z_fraction[n] = (zq - z[nz]) / (z[nz + 1] - z[nz])
                z_fraction_water_velocity[n] = z_fraction[n]

            elif nz > deepest_bottom_cell:
                # is in a layer above sea bed layer, and below top layer
                nz -= zq < z[nz]  # correction if zq falls in lower section of mapped interval containing fixed z level
                z_fraction[n] = (zq-z[nz])/(z[nz+1]-z[nz])
                z_fraction_water_velocity[n] = z_fraction[n]
            else:
                # in seabed layer, is variable thickness
                nz = deepest_bottom_cell
                dz = z[nz + 1] - z_bot # bottom layer thickness
                z_fraction[n] = (zq -z_bot) / dz
                z0p = z0 / dz # z0 as fraction of bottom layer
                z_fraction_water_velocity[n] = (np.log(z_fraction[n] + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

            # record new depth cell
            nz_cell[n] = nz
            #print('xx',zq,z_bot)
            xq[n, 2] = zq
        pass

def make_search_map(z):
    dz_map = 0.66 * np.min(abs(np.diff(z)))
    z_range = z[-1] - z[0]
    nz = int(np.ceil(z_range/ dz_map))  # number of levels in evenly map > number layers in z

    # insert a 1 at map levels containing a the hydro models z value, except the last
    sel = np.floor((z - z[0]) / dz_map).astype(np.int32)

    nz_map = np.zeros((nz,), dtype=np.int32)
    nz_map[sel[1:-1]] = 1  # dont include top and bottom in map
    nz_map = nz_map.cumsum()  # get layer offset from bottom at dz intervals

    return nz_map, dz_map
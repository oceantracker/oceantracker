from scipy.spatial import cKDTree
import numpy as np

from oceantracker.shared_info import shared_info as si
from oceantracker.util import basic_util
from oceantracker.util.profiling_util import function_profiler
from time import perf_counter
from oceantracker.util import numpy_util
from oceantracker.interpolator.util import  triangle_eval_interp
from oceantracker.particle_properties.util import  particle_operations_util
from oceantracker.util.numba_util import njitOT, njitOTparallel

import numba as nb

# globals to complile into numba to save pass arguments
psf = si.particle_status_flags
status_moving = int(psf.moving)
status_on_bottom = int(psf.on_bottom)
status_stranded_by_tide = int(psf.stranded_by_tide)

status_dead = int(psf.dead)
status_bad_coord = int(si.cell_search_status_flags.bad_coord)

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

        grid['sigma_nz_map'], grid['sigma_map_z'] = make_search_map(grid['sigma_interface'])


    def find_vertical_cell(self, fields, xq, current_buffer_steps, fractional_time_steps, active):
        # locate vertical cell in place
        part_prop = si.class_roles.particle_properties
        n_cell = part_prop['n_cell'].data
        status = part_prop['status'].data
        bc_coords = part_prop['bc_coords'].data
        grid = self.grid

        nz_cell = part_prop['nz_cell'].data
        z_fraction = part_prop['z_fraction'].data
        z_fraction_water_velocity = part_prop['z_fraction_water_velocity'].data

        bad_z_fraction_count = self.get_depth_cell_sigma_layers(xq,
                                    grid['triangles'],
                                    fields['water_depth'].data.ravel(),
                                    fields['tide'].data,
                                    si.settings.minimum_total_water_depth,
                                    grid['sigma_interface'], grid['sigma_nz_map'], grid['sigma_map_z'],
                                    n_cell, status, bc_coords, nz_cell, z_fraction, z_fraction_water_velocity,
                                    current_buffer_steps, fractional_time_steps,
                                    active, si.settings.z0)


        return bad_z_fraction_count

    @staticmethod
    @njitOTparallel
    def get_depth_cell_sigma_layers(xq, triangles, water_depth, tide, minimum_total_water_depth,
                                    sigma, sigma_map_nz,sigma_map_z,
                                    n_cell, status, bc_coords, nz_cell, z_fraction, z_fraction_water_velocity,
                                    current_buffer_steps, fractional_time_steps,
                                    active, z0):
        # view without redundant dim of 4D field
        tide1 = tide[current_buffer_steps[0], :, 0, 0]
        tide2 = tide[current_buffer_steps[1], :, 0, 0]
        frac0, frac1 = fractional_time_steps[0], fractional_time_steps[1]
        sigma_map_dz =  sigma_map_z[1] - sigma_map_z[0]

        bad_z_fraction_count = 0

        for nn in nb.prange(active.size):  # loop over active particles
            n = active[nn]
            nodes = triangles[n_cell[n], :]  # nodes for the particle's cell

            zq = float(xq[n, 2])

            # interp water depth
            z_bot = 0.
            for m in range(3):
                z_bot -= bc_coords[n, m] * water_depth[nodes[m]]

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
                z_top += bc_coords[n, m] * (tide1[nodes[m]] * frac0 + tide2[nodes[m]] * frac1)

            # clip z into range
            zq = min(max(zq, z_bot), z_top)

            twd = max(abs(z_top - z_bot), minimum_total_water_depth)
            zf = max(0., min(abs(zq - z_bot) / twd, 0.9999))  # with rounding keep, it just below surface, and at or above bottom

            # get  nz from evenly space sigma map, but zf always < 1, due to above
            nz_map = int(zf/sigma_map_dz)  # find index in map

            # get approx nz from map
            nz = sigma_map_nz[nz_map]

            # correction,  if zf is below  approx nz
            nz -= zf < sigma[nz]  # faster branch-less minus 1

            # get fraction within the sigma layer
            z_fraction[n] = (zf - sigma[nz]) / (sigma[nz + 1] - sigma[nz])
            bad_z_fraction_count +=  not  -0.05 <  z_fraction[n] < 1.05

            # make any already on bottom active, may be flagged on bottom if found on bottom below
            if status[n] == status_on_bottom:
                status[n] = status_moving

            # extra work if in bottom cell
            z_fraction_water_velocity[n] = z_fraction[n]
            pass
            if nz == 0:
                z0f = z0 / twd  # z0 as fraction of water depth
                # set status if on the bottom set status
                if zf < z0f:
                    # on bottom
                    status[n] = status_on_bottom
                    zq = z_bot
                    z_fraction_water_velocity[n] = 0.0
                else:
                    # adjust z fraction so that linear interp acts like log layer
                    z1 = (sigma[1] - sigma[0]) * twd  # dimensional bottom layer thickness
                    z0p = z0 / z1
                    z_fraction_water_velocity[n] = (np.log(z_fraction[n] + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

            # record new depth cell and z
            nz_cell[n] = nz
            xq[n, 2] = zq

        return bad_z_fraction_count

class FindVerticalCellSlayerLSCGrid(object):

    def __init__(self, grid, params):
        self.grid, self.params = grid, params
        self.info = {}
        self.walk_counts= np.zeros((2,), dtype=np.int64)

    def find_vertical_cell(self, fields, xq, current_buffer_steps, fractional_time_steps, active):
        part_prop = si.class_roles.particle_properties
        n_cell = part_prop['n_cell'].data
        status = part_prop['status'].data
        bc_coords = part_prop['bc_coords'].data
        grid = self.grid

        nz_cell = part_prop['nz_cell'].data
        z_fraction = part_prop['z_fraction'].data
        z_fraction_water_velocity = part_prop['z_fraction_water_velocity'].data

        bad_z_fraction_count = self.get_depth_cell_time_varying_Slayer_or_LSCgrid(xq,grid['triangles'], grid['z_interface'], grid['bottom_interface_index'],
                                                      n_cell, status, bc_coords, nz_cell, z_fraction, z_fraction_water_velocity,
                                                      current_buffer_steps, fractional_time_steps,
                                                      self.walk_counts,
                                                      active, si.settings.z0, part_prop['tide'].data)


        if False:
            # compare zlevel and tide
            import matplotlib.pyplot as plt
            plt.scatter(si.core_class_roles.field_group_manager.reader.fields['tide'].data[:,:,0,0],grid['z_interface'][:,:,-1],  c='b', s=.1)
            plt.grid('on')
            plt.show()

        return bad_z_fraction_count

    @staticmethod
    @njitOTparallel
    def get_depth_cell_time_varying_Slayer_or_LSCgrid(xq,
                                                      triangles, z_interface, bottom_interface_index,
                                                      n_cell, status, bc_coords, nz_cell, z_fraction, z_fraction_water_velocity,
                                                      current_buffer_steps, fractional_time_steps,
                                                      walk_counts,
                                                      active, z0,part_prop_tide):
        # find the zlayer for each node of cell containing each particle and at two time slices of hindcast  between nz_bottom and number of z levels
        # nz_with_bottom is the lowest cell in grid, is 0 for slayer vertical grids, but may be > 0 for LSC grids
        # nz_with_bottom must be time independent
        # vertical walk to search for a particle's layer in the grid, nz_cell

        def _eval_z_at_nz_cell(tf,nz_cell, z_interface1, z_interface2, nodes, nz_bottom_nodes, nz_top_cell, BCcord):
            # eval zlevel at particle location and depth cell, return z and nodes required for evaluation
            z = 0.
            for m in range(3):
                nz = max(min(nz_cell, nz_top_cell + 1), nz_bottom_nodes[m])  # move up to bottom, so not out of range
                z += BCcord[m] * (z_interface1[nodes[m], nz] * tf[0] + z_interface2[nodes[m], nz] * tf[1])
            return z

        nz_top_cell = z_interface.shape[2] - 2
        zl1 = z_interface[current_buffer_steps[0], ...]
        zl2 = z_interface[current_buffer_steps[1], ...]
        bad_z_fraction_count = 0

        bottom_nz_nodes = np.zeros((3,), dtype=np.int32)
        for nn in range(active.size):  # loop over active particles
            n = active[nn]
            bc = bc_coords[n, :]

            nodes = triangles[n_cell[n], :]  # nodes for the particle's cell

            deepest_bottom_cell = nz_top_cell
            for m in range(3):
                bottom_nz_nodes[m] = bottom_interface_index[nodes[m]]
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

            # find z_interface above and below  current vertical cell
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

            bad_z_fraction_count +=  not  -0.05 <  z_fraction[n] < 1.05

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
            xq[n, 2] = zq  # may differ if clipped into water depth range

            #if abs(zq-part_prop_tide[n]) > .2 and part_prop_tide[n] !=0 and n==0:
            #    print('xx debug vert cell find', zq, part_prop_tide[n],'below', z_below,'above', z_above)
            #    pass

            # step count stats, tidal stranded particles are not counted
            #walk_counts[0] += n_vertical_steps
            #walk_counts[1] = max(walk_counts[1], n_vertical_steps)  # record max number of steps

        return bad_z_fraction_count

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
        grid['nz_map'], grid['z_map'] = make_search_map(grid['z'])


    def find_vertical_cell(self, fields, xq, current_buffer_steps, fractional_time_steps, active):
        part_prop = si.class_roles.particle_properties
        n_cell = part_prop['n_cell'].data
        status = part_prop['status'].data
        bc_coords = part_prop['bc_coords'].data
        grid = self.grid

        nz_cell = part_prop['nz_cell'].data
        z_fraction = part_prop['z_fraction'].data
        z_fraction_water_velocity = part_prop['z_fraction_water_velocity'].data

        bad_z_fraction_count = self.get_depth_cell_fixedZ(xq, grid['triangles'], grid['bottom_interface_index'],
                             grid['water_depth'], fields['tide'].data, grid['z'], grid['nz_map'], grid['z_map'],
                             n_cell, status, bc_coords, nz_cell, z_fraction, z_fraction_water_velocity,
                             current_buffer_steps, fractional_time_steps,
                             active, si.settings.z0)
        return bad_z_fraction_count
    @staticmethod
    @njitOT
    def get_depth_cell_fixedZ(xq, triangles, bottom_interface_index,water_depth,tide,
                                    z, nz_map,z_map,
                                    n_cell, status, bc_coords, nz_cell, z_fraction, z_fraction_water_velocity,
                                    current_buffer_steps, fractional_time_steps,
                                    active, z0):
        dz_map_inv = 1.0/(z_map[1] - z_map[0])
        bad_z_fraction_count = 0

        for n in active:  # loop over active particles
            nodes = triangles[n_cell[n], :]  # nodes for the particle's cell
            zq = float(xq[n, 2])

            # interp to find water depth at particle location
            z_bot = 0.
            deepest_bottom_cell= nz_map[-1]
            for m in range(3):
                z_bot -= bc_coords[n, m] * water_depth[nodes[m]]
                # for ragged bottom, get the deepest cell a particle could be in amongst the 3 nodes
                deepest_bottom_cell = min(bottom_interface_index[nodes[m]],deepest_bottom_cell)

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
                z_top += bc_coords[n, m] * tide[current_buffer_steps[0], nodes[m], 0, 0] * fractional_time_steps[0]
                z_top += bc_coords[n, m] * tide[current_buffer_steps[1], nodes[m], 0, 0] * fractional_time_steps[1]

            zq = min(max(zq, z_bot), z_top) # clip to water depth and free surface
            n_in_map = int((zq - z[0])  * dz_map_inv) # number of map steps between zq and deepest fixed z in the map

            n_in_map = min(n_in_map,nz_map.size-1) # clip inside map
            nz = nz_map[n_in_map] # estimate of nz from map

            # correction, rounds down, so correct if z below z[nz]
            nz -= zq < z[nz]    # faster branch-less minus 1

            if nz > deepest_bottom_cell:
                # is in a layer above sea bed layer
                z1 = z[nz+1]  if nz < z.size-2 else z_top #  top cell needs tide not z[nz+1]
                z_fraction[n] = (zq-z[nz])/(z1-z[nz])
                z_fraction_water_velocity[n] = z_fraction[n]
            else:
                # in seabed layer, is variable thickness
                nz = deepest_bottom_cell
                dz = z[nz + 1] - z_bot # bottom layer thickness
                z_fraction[n] = (zq -z_bot) / dz
                z0p = z0 / dz # z0 as fraction of bottom layer
                z_fraction_water_velocity[n] = (np.log(z_fraction[n] + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))


            bad_z_fraction_count +=  not  (-0.05 <  z_fraction[n] < 1.05)

            # record new depth cell
            nz_cell[n] = nz
            xq[n, 2] = zq
        return bad_z_fraction_count

def make_search_map(z):

    dz_map = 0.66 * np.min(abs(np.diff(z))) # ensure map has smaller steps than smales z diffrence
    z_range = z[-1] - z[0]
    nz = int(np.ceil(z_range/ dz_map))  # number of levels in evenly map > number layers in z

    z_map = np.linspace(z[0], z[-1]+ dz_map/3, nz+1).astype(np.float64)

    # insert a 1 at map levels containing a  hydro models interface z value
    sel = np.floor((z - z_map[0]) / dz_map).astype(np.int32)
    nz_map = np.zeros((z_map.size,), dtype=np.int32)
    nz_map[sel] = 1
    # nz map rounds any interval containing a z down,
    nz_map = nz_map.cumsum() -1  # get layer offset from bottom at dz intervals

    # clip map to ensure >=0 and last z layer gets mapped down
    nz_map = np.maximum(np.minimum(nz_map, z.size-2), 0)
    # check map
    #  [(q, z[nz_map[q]],  nz_map[q],z_map[q]) for q in range(nz_map.size) ]
    return nz_map, z_map



class dev_FindVerticalCell_LSCv2(object):
    # this assumes fractional interface fractions vary between nodes, but not in time
    def __init__(self, grid, params):
        self.grid, self.params = grid, params
        self.info = {}
        self._make_sigma_depth_cell_search_map(grid)
        pass
    def _make_sigma_depth_cell_search_map(self, grid):
        # add lookup map to grid
        # setup lookup nz interval map of zfraction into with equal dz for finding vertical cell
        # the smalest sigms later thickness is at the bottom

        grid['sigma_nz_map'], grid['sigma_map_z'] = make_search_map(grid['sigma_interface'])


    def find_vertical_cell(self, fields, xq, current_buffer_steps, fractional_time_steps, active):
        # locate vertical cell in place
        part_prop = si.class_roles.particle_properties
        n_cell = part_prop['n_cell'].data
        status = part_prop['status'].data
        bc_coords = part_prop['bc_coords'].data
        grid = self.grid

        nz_cell = part_prop['nz_cell'].data
        z_fraction = part_prop['z_fraction'].data
        z_fraction_water_velocity = part_prop['z_fraction_water_velocity'].data

        bad_z_fraction_count= self.get_depth_cell_sigma_layers(xq,
                                    grid['triangles'],
                                    fields['water_depth'].data.ravel(),
                                    fields['tide'].data,
                                    si.settings.minimum_total_water_depth,
                                    grid['sigma_interface'], grid['sigma_nz_map'], grid['sigma_map_z'],
                                    n_cell, status, bc_coords, nz_cell, z_fraction, z_fraction_water_velocity,
                                    current_buffer_steps, fractional_time_steps,
                                    active, si.settings.z0)
        return bad_z_fraction_count

    @staticmethod
    @njitOTparallel
    def get_depth_cell(xq, triangles, water_depth, tide, minimum_total_water_depth,
                                    nodal_depth_fractions, nodal_sigma_map_nz,nodal_sigma_map_z,
                                    n_cell, status, bc_coords, nz_cell, z_fraction, z_fraction_water_velocity,
                                    current_buffer_steps, fractional_time_steps,
                                    active, z0):
        # view without redundant dim of 4D field
        tide1 = tide[current_buffer_steps[0], :, 0, 0]
        tide2 = tide[current_buffer_steps[1], :, 0, 0]
        frac0, frac1 = fractional_time_steps[0], fractional_time_steps[1]
        sigma_map_dz =  sigma_map_z[1] - sigma_map_z[0]

        bad_z_fraction_count = 0

        for nn in nb.prange(active.size):  # loop over active particles
            n = active[nn]
            nodes = triangles[n_cell[n], :]  # nodes for the particle's cell

            zq = float(xq[n, 2])

            # interp water depth
            z_bot = 0.
            for m in range(3):
                z_bot -= bc_coords[n, m] * water_depth[nodes[m]]

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
                z_top += bc_coords[n, m] * (tide1[nodes[m]] * frac0 + tide2[nodes[m]] * frac1)

            # clip z into range
            zq = min(max(zq, z_bot), z_top)

            twd = max(abs(z_top - z_bot), minimum_total_water_depth)
            zf = max(0., min(abs(zq - z_bot) / twd, 0.9999))  # with rounding keep, it just below surface, and at or above bottom

            # get  nz from evenly space sigma map, but zf always < 1, due to above
            nz_map = int(zf/sigma_map_dz)  # find index in map

            # get approx nz from map
            nz = sigma_map_nz[nz_map]

            # correction,  if zf is below  approx nz
            nz -= zf < sigma[nz]  # faster branch-less minus 1

            # get fraction within the sigma layer
            z_fraction[n] = (zf - sigma[nz]) / (sigma[nz + 1] - sigma[nz])
            bad_z_fraction_count +=  not  -0.05 <  z_fraction[n] < 1.05

            # make any already on bottom active, may be flagged on bottom if found on bottom below
            if status[n] == status_on_bottom:
                status[n] = status_moving

            # extra work if in bottom cell
            z_fraction_water_velocity[n] = z_fraction[n]
            pass
            if nz == 0:
                z0f = z0 / twd  # z0 as fraction of water depth
                # set status if on the bottom set status
                if zf < z0f:
                    # on bottom
                    status[n] = status_on_bottom
                    zq = z_bot
                    z_fraction_water_velocity[n] = 0.0
                else:
                    # adjust z fraction so that linear interp acts like log layer
                    z1 = (sigma[1] - sigma[0]) * twd  # dimensional bottom layer thickness
                    z0p = z0 / z1
                    z_fraction_water_velocity[n] = (np.log(z_fraction[n] + z0p) - np.log(z0p)) / (np.log(1. + z0p) - np.log(z0p))

            # record new depth cell and z
            nz_cell[n] = nz
            xq[n, 2] = zq

        return bad_z_fraction_count

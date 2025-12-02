import matplotlib.pyplot as plt

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.numba_util import  njitOT, njitOTparallel, prange
import numpy as np
from oceantracker.util import time_util
from oceantracker.shared_info import shared_info as si
from time import  perf_counter
from copy import copy, deepcopy

# run fields nested with outer main readers grid

class DevNestedFields(ParameterBaseClass):
    ''' Core class. Builds a list of field group managers for outer and nested grids and manages
    assignment to the different using a list of field group managers to carry out update, field interpolation etc
     First in list grid is the outer grid.
     Consistency between available hindcast variables means this code is fragile and error messages opaque.
     '''

    development = True

    def initial_setup(self, caller=None):

        ml = si.msg_logger
        info= self.info

        ml.msg('Nested grids only use geographic coords',warning=True,
               hint= 'Any hindcast not already in geographic coords must include a reader parameter "EPSG_code" to enable conversion, see https://spatialreference.org/')
        si.settings.use_geographic_coords = True

        # make outergrid field manager
        fgm_outer_grid = si.class_importer.make_class_instance_from_params('field_group_manager',
                           {}, default_classID='field_group_manager',
                               caller= self, crumbs='adding outer hydro-grid field manager for nested grid run')
        fgm_outer_grid.initial_setup(gridID=0,  caller=self)
        fgm_outer_grid.build_reader_fields()

        # outer grid is not required to have open boundary nodes, but can if provided
        if not fgm_outer_grid.info['has_open_boundary'] and si.settings.use_open_boundary:
            fgm_outer_grid.info['use_open_boundary'] = True

        # setup outer grid first and for presence of key reader fields in all hindcasts, outer first
        info['has_A_Z_profile'] = si.settings.use_A_Z_profile and fgm_outer_grid.info['has_A_Z_profile']
        info['has_bottom_stress']= si.settings.use_bottom_stress and fgm_outer_grid.info['has_bottom_stress']
        info['start_time']  = fgm_outer_grid.info['start_time']
        info['end_time'] = fgm_outer_grid.info['end_time']

        info['geographic_coords'] =  fgm_outer_grid.info['geographic_coords']
        info['is3D'] = fgm_outer_grid.info['is3D']

        # first grid is outer grid
        self.fgm_hydro_grids = [fgm_outer_grid]

        # add nested grids
        checks=dict(has_A_Z_profile=[],has_bottom_stress=[], is3D=[],geographic_coords=[], start_time=[],end_time=[],
                    input_dir=[],has_open_boundary=[])
        start_times = [info['start_time']]  # used to chech for overlaping times of all hindcasts
        end_times = [info['end_time']]

        for n, nr_params in enumerate(si.working_params['nested_readers']):
            ml.progress_marker(f'Starting nested grid setup #{len(self.fgm_hydro_grids)}')

            t0= perf_counter()
            fgm_nested =  si.class_importer.make_class_instance_from_params('field_group_manager', {}, default_classID='field_group_manager',
                                                 caller=caller, crumbs=f'adding nested hydro-model field manager #{len(self.fgm_hydro_grids)}')

            fgm_nested.initial_setup(gridID=n+1, caller=caller)
            fgm_nested.build_reader_fields()

            for key, item in checks.items():
                item.append(fgm_nested.info[key])

            # add to list of field_group managers
            self.fgm_hydro_grids.append(fgm_nested)
            start_times.append(fgm_nested.info['start_time'])
            end_times.append(fgm_nested.info['end_time'])

            ml.exit_if_prior_errors(f'failed to read nested reader #{n}, see above')

            if not fgm_nested.info['has_open_boundary']:
                ml.msg(f'Nested grids must have open boundary nodes defined, nested grid {n} " does not',
                                  fatal_error=True, hint= 'Need reader to load open boundary nodes, eg for Schsim, set reader parameter "hgrid_file" to load open boundary nodes')
            fgm_nested.info['use_open_boundary'] = True

            ml.progress_marker(f'Finished nested hydro-model grid setup #{len(self.fgm_hydro_grids)} '+
                   f'from {time_util.seconds_to_isostr(fgm_nested.info["start_time"])} to  {time_util.seconds_to_isostr(fgm_nested.info["end_time"])}', start_time=t0)

            # overlapping times checks
            info['start_time'] = max(start_times)
            info['end_time'] = min(end_times)

            if info['start_time'] >= info['end_time']:
                ml.msg(f'Some nested grid reader files do not overlap in time with the outer grid',
                       hint='check start s and ends if each grid above, or is file mask correct?', fatal_error=True)

            # build a mask of outer grid cells which may overlap this nested grid,
            # used when checking if particle on outer grid is now inside inner grid
            grid_outer = fgm_outer_grid.reader.grid
            outer_grid_cells_overlapping_inner_grid = np.full((grid_outer['triangles'].shape[0],),False, dtype= bool)

            # flag outer grid cells if any of its nodes are inside this nested grid
            for m in range(3):
                x_outer_grid =  grid_outer['x'][grid_outer['triangles'][:,m],:]
                sel_n, part_data_n = fgm_nested.are_points_inside_domain(x_outer_grid)
                outer_grid_cells_overlapping_inner_grid  = np.logical_or(sel_n,outer_grid_cells_overlapping_inner_grid )
            fgm_nested.reader.grid['outer_grid_cells_overlapping_inner_grid'] = outer_grid_cells_overlapping_inner_grid

            if False:
                # check overlaping cells of inner grid
                from matplotlib import pyplot as  plt
                plt.triplot(grid_outer['x'][:,0],grid_outer['x'][:,1], grid_outer['triangles'], c=[.8,.8,.8], lw=.1)
                plt.triplot(grid_outer['x'][:, 0], grid_outer['x'][:, 1],
                            grid_outer['triangles'][outer_grid_cells_overlapping_inner_grid,:], c=[.8, 0, 0], lw=.3)
                grid_nested = fgm_nested.reader.grid
                plt.triplot(grid_nested['x'][:, 0], grid_nested['x'][:, 1],  grid_nested['triangles'], c=[ 0,.8, 0],lw=.1)
                plt.show()

            pass


        # settings consistency with all hindcasts
        info['has_A_Z_profile'] = info['has_A_Z_profile'] and all(checks['has_A_Z_profile'])
        info['has_bottom_stress'] = info['has_bottom_stress'] and all(checks['has_bottom_stress'])

        if not all ([ x== info['is3D']for x in checks['is3D']]):
            ml.msg(f'Cannot mix 2D and 3D nestd grids ',
                   hint= f'For primary reader 3D ={info["is3D"]}, nested readers are 3D={str(checks["is3D"])}',
                   crumbs='Nested reader set up', fatal_error=True, caller=self)

        # dry cell flag
        if si.settings.write_dry_cell_flag:
            ml.msg(f'Cannot write dry cell flag to tracks files for nested grids, disabling dry cell writes',
                   crumbs='Nested reader set up ',  note=True)
            si.settings.write_dry_cell_flag = False


        #todo check out ant nested hindcasts over lap??
        pass

    def build_reader_fields(self):
        for n, fgm in  enumerate(self.fgm_hydro_grids):
            fgm.reader.build_fields()
        pass

    def final_setup(self):
        ml = si.msg_logger
        # do final setup for each grid
        for n, fgm in enumerate(self.fgm_hydro_grids):
            fgm.final_setup()


    def get_hindcast_info(self):
        d = dict(start_time=self.start_time,
                 end_time=self.end_time,
                 time_step=self.hydro_time_step )
        d['duration'] = d['end_time'] - d['start_time']
        d['start_date'] = time_util.seconds_to_isostr(d['start_time'])
        d['end_date'] = time_util.seconds_to_isostr(d['end_time'])
        d['date_span'] = time_util.seconds_to_pretty_duration_string(abs(d['end_time'] - d['start_time']))
        return d

    def update_readers(self, time_sec):
        for fgm in self.fgm_hydro_grids:
            fgm.update_readers(time_sec)

    def add_reader_field(self, name, params):
        for fgm in self.fgm_hydro_grids:
            fgm.add_reader_field(name, params)

    def add_custom_field(self, name, params, default_classID=None):
        for fgm in self.fgm_hydro_grids:
            fgm.add_custom_field(name, params, default_classID=default_classID)

    def add_part_prop_from_fields_plus_book_keeping(self):
        # only use outer grid to add properties for all readers
        for fgm in self.fgm_hydro_grids:
                fgm.add_part_prop_from_fields_plus_book_keeping()

    def are_points_inside_domain(self,x):
        # used to check initial release points only
        part_prop = si.class_roles.particle_properties

        # todo below look in all grids, starting with outer, faster to find first grid starting with nesteds
        # look find grid containing points, starting with last nested grid
        # do outer domain first, so oute has lowest prioity

        for n, fgm in enumerate(self.fgm_hydro_grids):

            sel_n, part_data_n = fgm.are_points_inside_domain(x)

            if n == 0:
                # start with outer grids values
                is_inside = sel_n.copy()
                part_data= deepcopy(part_data_n)
                part_data['hydro_model_gridID'][sel_n] = 0
            else:
                # use next grids values
                is_inside[sel_n]= True
                for name in part_data.keys():
                    part_data[name][sel_n,...] = part_data_n[name][sel_n,...]
                # put it in this grid
                part_data['hydro_model_gridID'][sel_n] = n


        return is_inside, part_data

    def release_are_dry_cells(self, release_info):
        # work out of dry for rreleased partivles
        sel = np.full((release_info['hydro_model_gridID'].size),False, dtype=bool)
        for ngrid, fgm in enumerate(self.fgm_hydro_grids):
            active   = release_info['hydro_model_gridID'] == ngrid
            sel[active] = fgm.reader.grid['dry_cell_index'][release_info['n_cell'][active]] > 128  # those dry

        return sel


    def interp_named_2D_scalar_fields_at_given_locations_and_time(self,field_name,  x, n_cell, bc_coords, time_sec = None, hydro_model_gridID = None):

        vals= np.full((x.shape[0],), 0., dtype=np.float32)

        # look through grids in reverse to find interpolated values, so use outer grid last
        for n in range(len(self.fgm_hydro_grids)):
            fgm = self.fgm_hydro_grids[n]
            sel = hydro_model_gridID == n
            vals[sel, ...] = fgm.interp_named_2D_scalar_fields_at_given_locations_and_time(field_name, x[sel, :],
                                          n_cell[sel],bc_coords[sel,:], time_sec= time_sec,hydro_model_gridID=n)
        #field_name, x, n_cell, bc_coords, time_sec = None, hydro_model_gridID = None
        return vals

    def setup_time_step(self, time_sec, xq, active):

        part_prop = si.class_roles.particle_properties

        # update outer grid
        fgm_outer_grid = self.fgm_hydro_grids[0]

        # todo make nested grid assignment faster by merging steps, requires numba kdtree find?
        on_outer_grid = part_prop['hydro_model_gridID'].find_subset_where(active, 'eq', 0, out=self.get_partID_buffer('fgmID0'))
        fgm_outer_grid.setup_time_step(time_sec, xq, on_outer_grid)

        # work through inner grids
        for n, fgm in enumerate(self.fgm_hydro_grids[1:],start=1):  # loop over nested grids

            # find any on outer grid that are now inside this inner grid
            # reduce use of slow initial cell find, by getting outer grid  subset  in outer grid cells overlapping innner grid
            on_outer_grid_overlapping_inner =  self._outer_overlapping_inner(fgm.reader.grid['outer_grid_cells_overlapping_inner_grid'],
                                                                           part_prop['n_cell'].data, on_outer_grid,  self.get_partID_buffer('fgmID1') )
            is_inside, pp = fgm.are_points_inside_domain(np.take(xq, on_outer_grid_overlapping_inner, axis=0))
            # todo faster way than using np.take??, use indices, rather than mask?

            if np.any(is_inside):
                # move those now inside outer grid and copy in values
                s = on_outer_grid_overlapping_inner[is_inside]
                part_prop['hydro_model_gridID'].set_values(n, s)  # put on inner grid
                part_prop['n_cell'].set_values(pp['n_cell'][is_inside], s)
                part_prop['n_cell_last_good'].set_values(pp['n_cell'][is_inside], s)
                part_prop['bc_coords'].set_values(pp['bc_coords'][is_inside, ...], s)

            # now update existing and those moved from outer to this inner grid
            on_inner_grid = part_prop['hydro_model_gridID'].find_subset_where(active, 'eq', n, out=self.get_partID_buffer('fgmID2'))

            # update inner grid,without fixing open boundary
            fgm.setup_time_step(time_sec, xq, on_inner_grid)

            # find those outside  this inner grid open boundary and move to outer
            outside_inner = part_prop['status'].find_subset_where(on_inner_grid, 'eq', si.particle_status_flags.outside_open_boundary,
                                                                  out=self.get_partID_subset_buffer('fgmID3'))
            if outside_inner.size > 0:
                inside_outer, pp = fgm_outer_grid.are_points_inside_domain(np.take(xq,outside_inner,axis =0))
                if np.any(inside_outer):
                    # move those now inside inner grid and copy in values
                    s = outside_inner[inside_outer]  # IDs of those outside inner and inside outer

                    part_prop['status'].set_values(si.particle_status_flags.moving, s)
                    part_prop['hydro_model_gridID'].set_values(0, s)  # put on outer grid
                    part_prop['n_cell'].set_values(pp['n_cell'][inside_outer], s)
                    part_prop['n_cell_last_good'].set_values(pp['n_cell'][inside_outer], s)
                    part_prop['bc_coords'].set_values(pp['bc_coords'][inside_outer, ...], s)

                    # update those now on outer grid and apply its open boundary condition
                    fgm_outer_grid.setup_time_step(time_sec, xq, s)
                    pass
                if np.any(~inside_outer):
                    fgm._move_back(outside_inner[~inside_outer] ) # move back to last good position on inner grid

            pass
            #todo any still outside the inner or outer grid? move back?
            #todo utside outer grid and all inner grids


        pass

    def interp_field_at_particle_locations(self, field_name, active, output=None):

        part_prop = si.class_roles.particle_properties

        for n, fgm in enumerate(self.fgm_hydro_grids):
            # find particles in this hydro-grid
            sel =  part_prop['hydro_model_gridID'].find_subset_where(active, 'eq', n, out=self.get_partID_subset_buffer('gridID')) # those on this grid

            fgm.interp_field_at_particle_locations(field_name, sel, output=output)
        pass


    def update_dry_cell_values(self):
        # loop over all hydro-models to update dry cellss
        for n, fgm in enumerate(self.fgm_hydro_grids):
            fgm.update_dry_cell_values()
        pass

    def update_tidal_stranding_status(self, time_sec, alive):
        # loop over grids

        part_prop = si.class_roles.particle_properties

        for n, fgm in enumerate(self.fgm_hydro_grids):
            # find particles in this hydro-grid
            sel = part_prop['hydro_model_gridID'].find_subset_where(alive, 'eq', n, out=self.get_partID_subset_buffer('gridID'))  # those on this grid
            fgm.tidal_stranding.update(fgm.reader.grid, time_sec, sel)

    def screen_info(self):
        # only for outer grid
        return self.fgm_hydro_grids[0].screen_info()

    def get_reader_info(self):
        d = dict(reader=self.fgm_hydro_grids[0].reader.info, nested_readers=[])
        for f in self.fgm_hydro_grids[1:]:
            d['nested_readers'].append(f.reader.info)
        return d

    @staticmethod
    @njitOT
    def _outer_overlapping_inner(outer_grid_cells_overlapping_inner_grid,n_cell, on_outer_grid, out):
         # check for any on the outer grid (indices=on_outer_grid) that are in that overlap the  inner grid,
        # this reduces number which must be tested to see it they are inside an inner grid triangle
        found_inside_inner = 0
        for n in on_outer_grid:
            if outer_grid_cells_overlapping_inner_grid[n_cell[n]]:
                out[found_inside_inner] = n
                found_inside_inner += 1

        return out[:found_inside_inner]

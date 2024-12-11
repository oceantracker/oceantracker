from oceantracker.field_group_manager.field_group_manager import FieldGroupManager
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util import time_util
from oceantracker.shared_info import shared_info as si
from time import  perf_counter
from copy import copy, deepcopy
from oceantracker.definitions import  cell_search_status_flags

# run fields nested with outer main readers grid

class DevNestedFields(ParameterBaseClass):
    ''' Core class. Builds a list of field group managers for outer and nested grids and manage
    interactions with list of field group managers. Eg update, interpolate etc
     First in list grid is the outer grid.
     Consistency between available hindcast variables means this code is fragile and error messages opaque.
     '''

    readers=[] # first is outer grid readers[0], nesting readers are readers[1:]

    def initial_setup(self,reader_builder,  caller=None):

        ml = si.msg_logger
        info= self.info
        # setup outer grid first and for presence of key reader fields in all hindcasts
        si.settings.use_bottom_stress = si.settings.use_bottom_stress and 'bottom_stress' in reader_builder['reader_field_info']
        si.settings.use_A_Z_profile = si.settings.use_A_Z_profile and 'A_Z_profile' in reader_builder['reader_field_info']

        fgm_outer_grid = si._class_importer.make_class_instance_from_params('field_group_manager', {}, default_classID='field_group_manager',
                               caller= caller, crumbs='adding outer hydro-grid field manager for nested grid run')
        fgm_outer_grid.initial_setup( reader_builder,  caller=self)

        hi = fgm_outer_grid.reader.info
        info.update(hi)

        # first grid is outer grid
        self.fgm_hydro_grids = [fgm_outer_grid]

        # add nested grids
        checks=dict(has_A_Z_profile=[],has_bottom_stress=[],is3D=[],geographic_coords=[], start_time=[],end_time=[],
                    input_dir=[])
        for rb in reader_builder['nested_reader_builders']:
            ml.progress_marker(f'Starting nested grid setup #{len(self.fgm_hydro_grids)}')

            t0= perf_counter()

            fgm_nested =  si._class_importer.make_class_instance_from_params('field_group_manager', {}, default_classID='field_group_manager',
                                                 caller=caller, crumbs=f'adding nested hydro-model field manager #{len(self.fgm_hydro_grids)}')
            fgm_nested.initial_setup(rb, caller=caller)

            for key, item in checks.items():
                item.append(fgm_nested.info[key])

            self.fgm_hydro_grids.append(fgm_nested)

            # note start and end times
            hi = fgm_nested.info
            info['start_time'] = max(info['start_time'],hi['start_time'])
            info['end_time']   = min(info['end_time'],  hi['end_time'])

            ml.progress_marker(f'Finished nested hydro-model grid setup #{len(self.fgm_hydro_grids)} '
                               f'from {time_util.seconds_to_isostr(hi["start_time"])} to  {time_util.seconds_to_isostr(hi["end_time"])}', start_time=t0)

        # overlapping times checks
        for  n, d in enumerate(zip(checks['start_time'],checks['end_time'], checks['input_dir'])):
            if not(d[0] <= info['start_time'] and  d[1] >= info['end_time']) :
                ml.msg(f'Nested reader files do not overlap in time with outer grid for files nested grid in # {d[2]}',
                       hint=f'Outer grid from {str(info["start_date"])}  to, {str(info["end_date"])},' +
                            f' inner grid from {time_util.seconds_to_isostr(d[0])}  to, {time_util.seconds_to_isostr(d[1])}',
                       fatal_error=True)
        ml.exit_if_prior_errors('Some non-overlapping times in nested grid hydro files')

        # settings consistency with hindcast
        info['has_A_Z_profile'] = info['has_A_Z_profile'] and all(checks['has_A_Z_profile'])
        info['has_bottom_stress'] = info['has_bottom_stress'] and all(checks['has_bottom_stress'])
        info['geographic_coords'] = info['geographic_coords'] or any(checks['geographic_coords'])

        if not all ([ x== info['is3D']for x in checks['is3D']]):
            ml.msg(f'Cannot mix 2D and 3D nestd grids ',
                   hint= f'For primary reader 3D ={info["is3D"]}, nested readers are 3D={str(checks["is3D"])}',
                   crumbs='Nested reader set up', fatal_error=True, exit_now=True, caller=self)

        #todo add check times overlaping

        # dry cell flag
        if si.settings['write_dry_cell_flag']:
            ml.msg(f'Cannot write dry cell flag to tracks files for nested grids, disabling dry cell writes',
                   crumbs='Nested reader set up ',  note=True)
            si.settings['write_dry_cell_flag'] = False

        #todo check hindcasts over lap

        pass

    def build_readers(self):
        for n, fgm in  enumerate(self.fgm_hydro_grids):
            fgm.reader.build_reader(gridID=n)
            fgm.reader.write_hydro_model_grid()
        pass


    def final_setup(self):

        ml = si.msg_logger
        # do final setup for each grid
        self.fgm_hydro_grids[0].final_setup()


        # check nested grids
        for n, fgm in enumerate(self.fgm_hydro_grids[1:]):
            fgm.final_setup()
            fgm.info['use_open_boundary'] = True  # force open boundary condition for inner grid
            if not fgm.info['has_open_boundary_nodes']:
                ml.msg(f'Nested grids must have open boundary nodes defined, nested grid {n} " does not',
                                  fatal_error=True, exit_now=True, hint= 'Need reader to load open boundary nodes, eg for Schsim, set reader parameter ""hgrid_file" to load open boundary nodes')

        # outer grid is not required to have open boundary nodes, but can if provided
        fgm = self.fgm_hydro_grids[0]
        if not fgm.info['has_open_boundary_nodes'] and si.settings.use_open_boundary: fgm.info['use_open_boundary'] = True
        pass


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

    def are_points_inside_domain(self,x,include_dry_cells):
        # used to check initial release points only
        part_prop = si.class_roles.particle_properties

        # todo below look in all grids, starting with outer, faster to find first grid starting with nesteds
        # look find grid containing points, starting with last nested grid
        # do outer domain first, so oute has lowest prioity
        for n, fgm in enumerate(self.fgm_hydro_grids):

            sel_n, part_data_n = fgm.are_points_inside_domain(x,include_dry_cells)

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


    def interp_named_2D_scalar_fields_at_given_locations_and_time(self,field_name,  x, n_cell, bc_cords, time_sec = None, hydro_model_gridID = None):

        vals= np.full((x.shape[0],), 0., dtype=np.float32)

        # look through grids in reverse to find interpolated values, so use outer grid last
        for n in range(len(self.fgm_hydro_grids)):
            fgm = self.fgm_hydro_grids[n]
            sel = hydro_model_gridID == n
            vals[sel, ...] = fgm.interp_named_2D_scalar_fields_at_given_locations_and_time(field_name, x[sel, :],
                                          n_cell[sel],bc_cords[sel,:], time_sec= time_sec,hydro_model_gridID=n)
        #field_name, x, n_cell, bc_cords, time_sec = None, hydro_model_gridID = None
        return vals

    def setup_time_step(self, time_sec, xq, active):

        part_prop = si.class_roles.particle_properties


        # update outer grid
        fgm_outer_grid = self.fgm_hydro_grids[0]
        on_outer_grid = part_prop['hydro_model_gridID'].find_subset_where(active, 'eq', 0, out=self.get_partID_buffer('fgmID0'))
        #print('xx1',on_outer_grid, part_prop['status'].data[:1], part_prop['x'].data[:1], part_prop['hydro_model_gridID'].data[:1])
        fgm_outer_grid.setup_time_step(time_sec, xq, on_outer_grid)

        # work through inner grids
        for n, fgm in enumerate(self.fgm_hydro_grids[1:],start=1):  # loop over nested rids

            # find any on outer grid that are now inside this inner grid
            # todo faster- prebuild a index to show which cells overlap with an  inner and only check if these are inside the inner grid

            is_inside, pp = fgm.are_points_inside_domain(np.take(xq, on_outer_grid, axis=0), include_dry_cells=True)

            if np.any(is_inside):
                # move those now inside outer grid and copy in values
                s = on_outer_grid[is_inside]

                #print('xx moved to inner grid',s[:2], part_prop['status'].data[s[:2]], part_prop['x'].data[s[:2]],  part_prop['hydro_model_gridID'].data[s[:2]])
                part_prop['hydro_model_gridID'].set_values(n, s)  # put on inner grid
                part_prop['n_cell'].set_values(pp['n_cell'][is_inside], s)
                part_prop['n_cell_last_good'].set_values(pp['n_cell'][is_inside], s)
                part_prop['bc_cords'].set_values(pp['bc_cords'][is_inside, ...], s)
                on_outer_grid = on_outer_grid[~is_inside]  # found a grid so drop from consideration of moving to another inner grid

            # now update existing and those moved from outer to this inner grid
            on_inner_grid = part_prop['hydro_model_gridID'].find_subset_where(active, 'eq', n, out=self.get_partID_buffer('fgmID1'))

            # update inner grid,without fixing open boundary
            fgm.setup_time_step(time_sec, xq, on_inner_grid)

            # find those outside  this inner grid open boundary and move to outer
            outside_inner = part_prop['status'].find_subset_where(on_inner_grid, 'eq', si.particle_status_flags.outside_open_boundary, out=self.get_partID_subset_buffer('fgmID2'))
            if outside_inner.size > 0:
                inside_outer, pp = fgm_outer_grid.are_points_inside_domain(np.take(xq,outside_inner,axis =0), include_dry_cells=True)
                if np.any(inside_outer):
                    # move those now inside inner grid and copy in values
                    s = outside_inner[inside_outer]  # IDs of those outside inner and inside outer


                    part_prop['status'].set_values(si.particle_status_flags.moving, s)
                    part_prop['hydro_model_gridID'].set_values(0, s)  # put on outer grid
                    part_prop['n_cell'].set_values(pp['n_cell'][inside_outer], s)
                    part_prop['n_cell_last_good'].set_values(pp['n_cell'][inside_outer], s)
                    part_prop['bc_cords'].set_values(pp['bc_cords'][inside_outer, ...], s)
                    #print('xx moved to outer grid', s[:2], part_prop['status'].data[s[:2]], part_prop['x'].data[s[:2]],  part_prop['hydro_model_gridID'].data[:1])
                    # update those now on outer grid and apply its open boundary condition
                    fgm_outer_grid.setup_time_step(time_sec, xq, s)
                    pass
                if np.any(~inside_outer):
                    fgm._move_back(outside_inner[~inside_outer] ) # move back to last good position on inner grid
                    #part_prop['hydro_model_gridID'].set_values(-1,outside_inner[~inside_outer] )
                    #print('xx could not be moved to outer grid=',n,'count=', np.count_nonzero(~inside_outer))
            pass
            #print('xx10', part_prop['status'].data[:1], part_prop['x'].data[:1],    part_prop['hydro_model_gridID'].data[:1])
            #todo any still outside the inner or outer grid? move back?
            #todo utside outer grid and all inner grids
        pass

    def interp_field_at_particle_locations(self, field_name, active, output=None):

        # loop over grids find interpolated values

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



from oceantracker.field_group_manager.field_group_manager import FieldGroupManager
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util import time_util
from oceantracker.shared_info import SharedInfo as si
from time import  perf_counter
from copy import copy, deepcopy
from oceantracker.definitions import  cell_search_status_flags

# run fields nested with outer main readers grid

class DevNestedFields(ParameterBaseClass):
    # build a list of field group managers for outer and nest grids
    # first in list grid is the outer grid

    readers=[] # first is outer grid, nesting the others

    def initial_setup(self):

        ml = si.msg_logger
        # setup outer grid first

        if si.settings.write_tracks:
            pass

        fgm_outer_grid = si._class_importer.new_make_class_instance_from_params('field_group_manager',dict(class_name='oceantracker.field_group_manager.field_group_manager.FieldGroupManager'),
                                                                                crumbs='adding outer hydro-grid field manager for nested grid run')
        fgm_outer_grid.initial_setup()
        hi = fgm_outer_grid.get_hindcast_info()
        self.hydro_time_step = hi['time_step']
        self.start_time, self.end_time = hi['start_time'], hi['end_time']
        self.grid['is3D'] = fgm_outer_grid.info['is3D']

        # todo  check if all hindcasts have same required info


        # first grid is outer grid
        self.fgm_hydro_grids = [fgm_outer_grid]

        # add nested grids
        for name, rb in si.run_builder['nested_reader_builders'].items():
            ml.progress_marker(f'Starting nested grid setup #{len(self.fgm_hydro_grids)}, name= "{name}"')

            t0= perf_counter()
            fgm_nested =  si._class_importer.new_make_class_instance_from_params('field_group_manager',dict(class_name='oceantracker.field_group_manager.field_group_manager.FieldGroupManager'),
                                                     crumbs=f'adding nested hydro-model field manager #{len(self.fgm_hydro_grids)}')

            fgm_nested._setup_hydro_reader(rb)

            # todo check that all nested grids have open bc and set open to true
            fgm_nested.set_up_interpolator()


            self.fgm_hydro_grids.append(fgm_nested)

            # note times
            hi = fgm_nested.get_hindcast_info()
            self.hydro_time_step = min(self.hydro_time_step,hi['time_step'])

            # start and end times
            self.start_time, self.end_time=  max(self.start_time,hi['start_time']), min(self.end_time,hi['end_time'])

            ml.progress_marker(f'Finished nested hydro-model grid setup #{len(self.fgm_hydro_grids)}, name= "{name}", '
                               f'from {time_util.seconds_to_isostr(hi["start_time"])} to  {time_util.seconds_to_isostr(hi["end_time"])}', start_time=t0)

        #todo add check times overlaping

        # dry cell flag
        if si.settings['write_dry_cell_flag']:
            ml.msg(f'Cannot write dry cell flag to tracks files for nested grids, disabling dry cell writes',
                   crumbs='Nested reader set up ',  note=True)
            si.settings['write_dry_cell_flag'] = False

        #todo check hindcasts over lap

        pass

    def final_setup(self):

        ml = si.msg_logger
        # do final setup for each grid
        for fgm in self.fgm_hydro_grids:
            fgm.final_setup()
            fgm.info['open_boundary_type'] = 1 # do nothing open boundary condition for inner grids

        # check nested grids
        for n, fgm in enumerate(self.fgm_hydro_grids[1:],start=1):
            if not fgm.info['has_open_boundary_nodes']:
                ml.msg(f'Nested grids must tag open boundary nodes, nested grid {n+1} " does not',
                                  fatal_error=True, exit_now=True, hint= 'Need reader to load open boundary nodes, eg for Schsim, set reader parameter ""hgrid_file" to load open boundary nodes')

        # outer grid is not required to have open boundary nodes, but can if provided
        fgm = self.fgm_hydro_grids[0]
        if not fgm.info['has_open_boundary_nodes']: fgm.info['open_boundary_type'] = si.settings.open_boundary_type
        pass

    def setup_dispersion_and_resuspension_fields(self):
        # see if al files have the required variables

        ml = si.msg_logger
        has_bottom_stress = []
        has_A_Z_profile  = []

        # check each file
        for fgm in self.fgm_hydro_grids:
            nc = fgm.reader.open_first_file()
            fmap = fgm.reader.params['field_variable_map']

            # see if A_z profile variablve present to use in vertical dispersion
            has_A_Z_profile.append(si.run_info.is3D_run and si.settings['use_A_Z_profile'] and fmap['A_Z_profile'] is not None and nc.is_var(fmap['A_Z_profile']) )
            # use bottom stres for resupension if in all files
            if si.run_info.is3D_run:
                # add friction velocity from bottom stress or near seabed vel
                bs_map = fmap['bottom_stress'] if type(fmap['bottom_stress']) == list else [fmap['bottom_stress']]  # ensure map is a list
                has_bottom_stress.append(nc.is_var(bs_map[0]))
        pass

        # acheck all hydro models have bootom stress
        if all(has_bottom_stress):
            # set up additional fields
            has_bottom_stress = True
        else:
            has_bottom_stress = False
            ml.msg('Not all hydro-models have bottom stress variable, using near seabed velocity to calculate friction velocity for resuspension ',note=True)

        # check al have Az profile
        if all(has_A_Z_profile):
            # set up additional fields
            has_A_Z_profile = True
        else:
            has_A_Z_profile = False
            ml.msg('Not 3D run, or not all hydro-models have A_Z profile, using constant A_Z for vertical dispersion' , note=True)

        self.info['has_A_Z_profile'] = has_A_Z_profile

        for fgm in self.fgm_hydro_grids:
            fgm._setup_required_resupension_fields(nc, has_bottom_stress)
            fgm._setup_required_dispersion_fields(nc, has_A_Z_profile)

        nc.close()

    def get_hindcast_info(self):
        d = dict(start_time=self.start_time,
                 end_time=self.end_time,
                 time_step=self.hydro_time_step )
        d['duration'] = d['end_time'] - d['start_time']
        d['start_date'] = time_util.seconds_to_isostr(d['start_time'])
        d['end_date'] = time_util.seconds_to_isostr(d['end_time'])
        d['date_span'] = time_util.seconds_to_pretty_duration_string(abs(d['end_time'] - d['start_time']))
        return d

    def update_reader(self, time_sec):

        for fgm in self.fgm_hydro_grids:
            fgm.update_reader(time_sec)


    def get_hydo_model_time_step(self): return self.hydro_time_step # return the smallest time step

    def get_hindcast_start_end_times(self):
        return self.start_time, self.end_time

    def add_part_prop_from_fields_plus_book_keeping(self):
        # only use outer grid to add properties for all readers
        self.fgm_hydro_grids[0].add_part_prop_from_fields_plus_book_keeping()

    def are_points_inside_domain(self,x,include_dry_cells):
        # used to check initial release points only
        part_prop = si.roles.particle_properties

        # todo below look in all grids, starting with outer, faster to find first grid starting with nesteds
        # look find grid containing points, starting with last nested grid
        # do outer domain first, so oute has lowest prioity
        for n, fgm in enumerate(self.fgm_hydro_grids):

            sel_n, part_data_n = fgm.are_points_inside_domain(x,include_dry_cells)

            if n == 0:
                # start with outer grids values
                is_inside = sel_n.copy()
                part_data= deepcopy(part_data_n)
            else:
                # use next grids values
                is_inside[sel_n]= True
                for name in part_data.keys():
                    part_data[name][sel_n,...] = part_data_n[name][sel_n,...]
                # put it in this grid
                part_data['hydro_model_gridID'][sel_n] = n


        return is_inside, part_data


    def interp_named_field_at_given_locations_and_time(self, field_name, x, time_sec= None, n_cell=None,bc_cords=None, output=None,hydro_model_gridID=None):

        vals= np.full((x.shape[0],), 0., dtype=np.float32)

        # look through grids in reverse to find interpolated values, so use outer grid last
        for n in range(len(self.fgm_hydro_grids)):
            fgm = self.fgm_hydro_grids[n]
            sel = hydro_model_gridID == n
            vals[sel, ...] = fgm.interp_named_field_at_given_locations_and_time(field_name, x[sel, :],
                                          time_sec=time_sec, n_cell=n_cell[sel], bc_cords=bc_cords[sel, :])

        return vals

    def setup_time_step(self, time_sec, xq, active):

        part_prop = si.roles.particle_properties


        # update outer grid
        fgm_outer_grid = self.fgm_hydro_grids[0]
        on_outer_grid = part_prop['hydro_model_gridID'].find_subset_where(active, 'eq', 0, out=self.get_partID_buffer('fgmID0'))
        fgm_outer_grid.setup_time_step(time_sec, xq, on_outer_grid, apply_open_boundary_condition=True)

        # work through inner grids
        for n, fgm in enumerate(self.fgm_hydro_grids[1:],start=1):  # loop over nested rids

            # find any on outer grid that are now inside this inner grid
            # todo faster- prebuild a index to show which cells overlap with an  inner and only check if these are inside the inner grid

            is_inside, pp = fgm.are_points_inside_domain(np.take(xq, on_outer_grid, axis=0), include_dry_cells=True)

            if np.any(is_inside):
                # move those now inside inner grid and copy in values
                s = on_outer_grid[is_inside]
                #print('xx moved to inner grid', n, np.count_nonzero(is_inside), int(time_sec),part_prop['ID'].get_values(s[:5]))

                part_prop['hydro_model_gridID'].set_values(n, s)  # put on inner grid
                part_prop['n_cell'].set_values(pp['n_cell'][is_inside], s)
                part_prop['n_cell_last_good'].set_values(pp['n_cell'][is_inside], s)
                part_prop['bc_cords'].set_values(pp['bc_cords'][is_inside, ...], s)
                on_outer_grid = on_outer_grid[~is_inside]  # found a grid so drop from consideration of moving to another inner grid

            # now update existing and those moved from outer to this inner grid
            on_inner_grid = part_prop['hydro_model_gridID'].find_subset_where(active, 'eq', n, out=self.get_partID_buffer('fgmID1'))

            # update inner grid,without fixing open boundary
            fgm.setup_time_step(time_sec, xq, on_inner_grid, apply_open_boundary_condition=False)

            # find those outside  this inner grid open boundary and move to outer
            outside_inner = part_prop['cell_search_status'].find_subset_where(on_inner_grid, 'eq', cell_search_status_flags.open_boundary_edge, out=self.get_partID_subset_buffer('fgmID2'))
            if outside_inner.size > 0:
                inside_outer, pp = fgm_outer_grid.are_points_inside_domain(np.take(xq,outside_inner,axis =0), include_dry_cells=True)
                if np.any(inside_outer):
                    # move those now inside inner grid and copy in values
                    s = outside_inner[inside_outer]  # IDs of those outside inner and inside outer
                    #print('xx moved to outer grid=', n,'count=', np.count_nonzero(inside_outer), int(time_sec),part_prop['ID'].get_values(s[:5]))

                    part_prop['status'].set_values(si.particle_status_flags.moving, s)
                    part_prop['hydro_model_gridID'].set_values(0, s)  # put on outer grid
                    part_prop['n_cell'].set_values(pp['n_cell'][inside_outer], s)
                    part_prop['n_cell_last_good'].set_values(pp['n_cell'][inside_outer], s)
                    part_prop['bc_cords'].set_values(pp['bc_cords'][inside_outer, ...], s)

                    # update those now on outer grid and apply its open boundary condition
                    fgm_outer_grid.setup_time_step(time_sec, xq, s, apply_open_boundary_condition=True)
                    pass
                if np.any(~inside_outer):
                    fgm._move_back(outside_inner[~inside_outer] ) # move back to last good position on inner grid
                    #part_prop['hydro_model_gridID'].set_values(-1,outside_inner[~inside_outer] )
                    #print('xx could not be moved to outer grid=',n,'count=', np.count_nonzero(~inside_outer))

            #todo any still outside the inner or outer grid? move back?
            #todo utside outer grid and all inner grids
        pass

    def interp_field_at_particle_locations(self, field_name, active, output=None):

        # loop over grids find interpolated values

        part_prop = si.roles.particle_properties

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

        part_prop = si.roles.particle_properties

        for n, fgm in enumerate(self.fgm_hydro_grids):
            # find particles in this hydro-grid
            sel = part_prop['hydro_model_gridID'].find_subset_where(alive, 'eq', n, out=self.get_partID_subset_buffer('gridID'))  # those on this grid
            fgm.tidal_stranding.update(fgm.grid, time_sec, sel)



    def screen_info(self):
        # only for outer grid
        return self.fgm_hydro_grids[0].screen_info()

    def write_hydro_model_grid(self):
        # loop over all hydro-models to write grids
        for n, fgm in enumerate(self.fgm_hydro_grids):
            fgm.write_hydro_model_grid(gridID=n)

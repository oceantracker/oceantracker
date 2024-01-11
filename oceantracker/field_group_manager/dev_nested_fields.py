from oceantracker.field_group_manager.field_group_manager import FieldGroupManager
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.field_group_manager.util import  field_group_manager_util
import numpy as np
from oceantracker.util.parameter_util import make_class_instance_from_params
from oceantracker.util.time_util import seconds_to_isostr
from time import  perf_counter
from copy import copy
# run fields nested with outer main readers grid

class DevNestedFields(ParameterBaseClass):
    # build a list of field group managers for outer and nest grids
    # first in list grid is the outer grid

    readers=[] # first is outer grid, nesting the others

    def initial_setup(self):
        si = self.shared_info
        ml = si.msg_logger
        # setup outer grid first


        fgm_outer_grid = make_class_instance_from_params('field_group_manager_outer_grid',
                                dict(class_name='oceantracker.field_group_manager.field_group_manager.FieldGroupManager'),
                                ml,   crumbs='adding outer hydro-grid field manager for nested grid run' )
        fgm_outer_grid.initial_setup()

        # note es to check if all hidcasts have same required info

        self.hydro_time_step = fgm_outer_grid.get_hydo_model_time_step()
        self.start_time, self.end_time  = fgm_outer_grid.get_hindcast_start_end_times()

        # first grid is outer grid
        self.fgm_hydro_grids = [fgm_outer_grid]

        # add nested grids
        for name, params in si.working_params['nested_reader_builders'].items():
            ml.progress_marker(f'Starting nested grid setup #{len(self.fgm_hydro_grids)}, name= "{name}"')

            t0= perf_counter()
            i =  make_class_instance_from_params(name,
                                                 dict(class_name='oceantracker.field_group_manager.field_group_manager.FieldGroupManager'),
                                                 ml, crumbs=f'adding nested hydro-model field manager #{len(self.fgm_hydro_grids)}')

            i._setup_hydro_reader(params)

            # todo check that all nested grids have open bc and set open to true
            i.set_up_interpolator()


            self.fgm_hydro_grids.append(i)

            # note times

            self.hydro_time_step = min(self.hydro_time_step,i.get_hydo_model_time_step())

            # start and end times
            times= i.get_hindcast_start_end_times()
            self.start_time, self.end_time=  max(self.start_time,times[0]), min(self.end_time,times[1])

            ml.progress_marker(f'Finished nested hydro-model grid setup #{len(self.fgm_hydro_grids)}, name= "{name}", from {seconds_to_isostr(times[0])} to  {seconds_to_isostr(times[1])}', start_time=t0)

        #todo add check times overlaping

        # dry cell flag
        if si.settings['write_dry_cell_flag']:
            ml.msg(f'Cannot write dry cell flag to tracks files for nested grids, disabling dry cell writes',
                   crumbs='Nested reader set up ',  note=True)
            si.settings['write_dry_cell_flag'] = False

        #todo check hindcasts over lap

        pass

    def final_setup(self):
        si = self.shared_info

        # do final setup for each grid
        for fgm in self.fgm_hydro_grids:
            fgm.final_setup()

        # ensure nested grids have open boundary data and set open boundary type
        if si.settings['open_boundary_type'] == 0:
            si.msg_logger.msg('For nested grids must set "open_boundary_type" must be > to select an open boundary type', fatal_error=True, exit_now=True)

        # check nested grids
        for n, fgm in enumerate(self.fgm_hydro_grids[1:]):
            if not fgm.info['has_open_boundary_nodes']:
                si.msg_logger.msg(f'Nested grids must tag open boundary nodes, nested grid {n+1} " does not',
                                  fatal_error=True, exit_now=True, hint= 'Need reader to load open boundary nodes, eg for Schsim, set reader parameter ""hgrid_file" to load open boundary nodes')

        # outer grid is not required to have open boundary nodes, but can if provided
        fgm = self.fgm_hydro_grids[0]
        if  not fgm.info['has_open_boundary_nodes']: fgm.info['open_boundary_type'] = 0
        pass


    def setup_dispersion_and_resuspension(self):
        # see if al files have the required variables
        si = self.shared_info
        ml = si.msg_logger
        has_bottom_stress = []
        has_A_Z_profile  = []

        # check each file
        for fgm in self.fgm_hydro_grids:
            nc = fgm.reader.open_first_file()
            fmap = fgm.reader.params['field_variable_map']

            # see if A_z profile variablve present to use in vertical dispersion
            has_A_Z_profile.append(si.is3D_run and si.settings['use_A_Z_profile'] and fmap['A_Z_profile'] is not None and nc.is_var(fmap['A_Z_profile']) )
            # use bottom stres for resupension if in all files
            if si.is3D_run:
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
            fgm._setup_resupension(nc, has_bottom_stress)
            fgm._setup_dispersion(nc, has_A_Z_profile)

        nc.close()

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
        si = self.shared_info
        part_prop = si.classes['particle_properties']
        # set up space
        N= x.shape[0]
        is_inside= np.full((N,),False)
        n_cell    = np.full((N,), si.particle_status_flags['unknown'],dtype=np.int32)
        bc  = np.full((N,3), -1, dtype=np.float64)
        hydro_model_gridID = np.full((N,), -1, dtype=np.int8)

        # look find grid containing points, starting with last nested grid
        # do outer domain last, so do in reverse order
        for n in reversed(range(len(self.fgm_hydro_grids))):
            i = self.fgm_hydro_grids[n]
            index = np.flatnonzero(~is_inside) # those not yet found inside inner grid

            sel, n_cell_n, bc_n, ingore_gridID = i.are_points_inside_domain(x[index,:],include_dry_cells)

            #record those inside this grid
            index = index[sel]
            is_inside[index] = True
            n_cell[index] = n_cell_n[sel]
            bc[index] = bc_n[sel,:]
            hydro_model_gridID[index] = n
            pass

        return is_inside, n_cell, bc, hydro_model_gridID


    def interp_named_field_at_given_locations_and_time(self, field_name, x, time_sec= None, n_cell=None,bc_cords=None, output=None,hydro_model_gridID=None):

        vals= np.full((x.shape[0],), 0., dtype=np.float32)

        # look through grids in reverse to find interpolated values, so use outer grid last
        for n in reversed(range(len(self.fgm_hydro_grids))):
            i = self.fgm_hydro_grids[n]
            sel = hydro_model_gridID ==  n
            vals[sel, ...] = i.interp_named_field_at_given_locations_and_time(field_name, x[sel, :],
                                          time_sec=time_sec, n_cell=n_cell[sel], bc_cords=bc_cords[sel, :], output=output, hydro_model_gridID=hydro_model_gridID[sel])

        return vals

    def setup_time_step(self, time_sec, xq, active, fix_bad=True):
        si= self.shared_info
        part_prop=  si.classes['particle_properties']

        #todo make faster with id buffers

        # loop over nested grids to find those outside their domains
        for n in range(1, len(self.fgm_hydro_grids)):
            fgm = self.fgm_hydro_grids[n]

            # get particles currently on this hydro grid
            sel =np.flatnonzero(part_prop['hydro_model_gridID'].data == n)
            fgm.setup_time_step(time_sec, xq, sel, fix_bad=fix_bad)
            # find those outside that were on this grid but are now not outside the open boundary
            outside_domain = part_prop['status'].find_subset_where(sel, 'eq', si.particle_status_flags['outside_open_boundary'])

            # try to move any outside the nested grids open boundary to the outer grid
            is_inside, n_cell, bc, hydro_model_gridID = self.fgm_hydro_grids[0].are_points_inside_domain(xq[outside_domain,:], not si.settings['block_dry_cells'])
            sel_outer = outside_domain[is_inside]
            part_prop['hydro_model_gridID'].set_values(0,sel_outer)
            part_prop['n_cell'].set_values(n_cell[is_inside], sel_outer)
            part_prop['n_cell_last_good'].set_values(n_cell[is_inside], sel_outer)
            part_prop['bc_cords'].set_values(bc[is_inside,:], sel_outer)
            part_prop['bc_cords'].set_values(bc[is_inside, :], sel_outer)

            #todo move back those outside iand not inside outer domain
            if np.any(~is_inside):
                pass
                print( f'xxxxx  particles {str(np.count_nonzero(~is_inside))} outside inner domain {n:3d} are also outside outer grid')



        # now setup those on outer grid, check hori cell and add vertical cell
        sel = np.flatnonzero(part_prop['hydro_model_gridID'].data == 0)
        self.fgm_hydro_grids[0].setup_time_step(time_sec, xq, sel, fix_bad=fix_bad)

        #todo find those in outside grid now in inner grid

        pass

    def interp_field_at_particle_locations(self, field_name, active, output=None):

        # loop over grids find interpolated values
        si = self.shared_info
        part_prop = si.classes['particle_properties']

        for n, fgm in enumerate(self.fgm_hydro_grids):
            # find particles in this hydro-grid
            sel =  part_prop['hydro_model_gridID'].find_subset_where(active, 'eq', n, out=self.get_partID_subset_buffer('gridID')) # those on this grid
            fgm.interp_field_at_particle_locations(field_name, sel, output=output)
        pass


    def update_dry_cell_index(self):
        # loop over all hydro-models to update dry cellss
        for n, fgm in enumerate(self.fgm_hydro_grids):
            fgm.update_dry_cell_index()
        pass

    def update_tidal_stranding_status(self, time_sec, alive):
        # loop over grids
        si = self.shared_info
        part_prop = si.classes['particle_properties']

        for n, fgm in enumerate(self.fgm_hydro_grids):
            # find particles in this hydro-grid
            sel = part_prop['hydro_model_gridID'].find_subset_where(alive, 'eq', n, out=self.get_partID_subset_buffer('gridID'))  # those on this grid
            fgm.tidal_stranding.update(fgm.grid, time_sec, sel)


    def fix_time_step(self, alive):
        # loop over grids
        si = self.shared_info
        part_prop = si.classes['particle_properties']

        for n, fgm in enumerate(self.fgm_hydro_grids):
            # find particles in this hydro-grid
            sel = part_prop['hydro_model_gridID'].find_subset_where(alive, 'eq', n, out=self.get_partID_subset_buffer('gridID'))  # those on this grid
            fgm.fix_time_step(sel)

    def screen_info(self):
        # only for outer grid
        return self.fgm_hydro_grids[0].screen_info()

    def write_hydro_model_grid(self):
        # loop over all hydro-models to write grids
        for n, fgm in enumerate(self.fgm_hydro_grids):
            fgm.write_hydro_model_grid(gridID=n)

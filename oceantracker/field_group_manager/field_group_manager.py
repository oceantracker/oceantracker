from oceantracker.util.parameter_base_class import ParameterBaseClass
import numpy as np
from time import perf_counter
from oceantracker.field_group_manager.util import field_group_manager_util
from oceantracker.shared_info import shared_info as si
from oceantracker.interpolator.util import  triangle_eval_interp
from oceantracker.field_group_manager import setup_reader

class FieldGroupManager(ParameterBaseClass):
    # class holding data in file and ability to spatially interpolate fields that it holds
    #   all the fields in a file and interpolation which belongs to the set of fields (rather than individual variable)
    # works with 2D or 3D  with appropriate interplotor

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.n_buffer = np.zeros((2, ), dtype=np.int32)

        info = self.info
        info['current_hydro_model_step']= 0
        info['fractional_time_steps']= np.zeros((2,), dtype=np.float64)
        info['current_buffer_steps'] = np.zeros((2,), dtype=np.int32)

    def initial_setup(self,gridID=0,  caller=None):

        ml = si.msg_logger
        info = self.info
        info['gridID'] = gridID

        # get params from main or nested reader
        if gridID > 0:
            reader_params = si.working_params['nested_readers'][gridID - 1]
        else:
            reader_params = si.working_params['reader']

        self.reader, add_info = self._make_a_reader(reader_params)

        if gridID == 0:
            si.core_class_roles.reader = self.reader
        else:
            si.class_roles.nested_readers[f'nested_reader_{gridID:02d}'] = self.reader

        info.update(add_info)

    def build_reader_fields(self):
        reader = self.reader
        reader.build_fields()

        # todo add ancillary field readers here, eg waves

    def final_setup(self):
        ml = si.msg_logger
        info = self.info
        grid = self.reader.grid

        if 'use_open_boundary' not in info :
            # set info here if not preset by nested grids
            info['use_open_boundary'] = si.settings.use_open_boundary

        # set up dry cell adjacency space for triangle walk
        grid['adjacency_with_dry_edges'] = grid['adjacency'].copy()  # working space to add dry cell boundaries to

        self.reader.interpolator.final_setup()

        # add tidal stranding class
        i = si.add_class('tidal_stranding', {}, crumbs=f'field Group Manager>setup_hydro_fields> tidal standing setup ', caller=self)
        self.tidal_stranding = i

        # write_grid
        self.reader.write_grid(info['gridID'])

        pass
        if si.settings.display_grid_at_start:
            from matplotlib import pyplot as plt
            from oceantracker.plot_output.plot_utilities import display_grid
            display_grid(grid, 1)
            plt.show()

    def add_reader_field(self,name, params):
        r = self.reader
        r._add_a_reader_field(name, params)

    def add_custom_field(self,name, params, default_classID=None):
        # todo move to reader??
        r = self.reader
        i = si.class_importer.make_class_instance_from_params('fields',params, name=name,
            add_required_classes_and_settings=False,      default_classID=default_classID)
        i.add_required_classes_and_settings(r.info)   # add classes required by this class
        i.initial_setup(r.info)
        r.fields[name] = i

    def add_part_prop_from_fields_plus_book_keeping(self):
        # add part prop for reader and custom fields
        for name, i in self.reader.fields.items():
            if i.params['create_particle_property_with_same_name']:
                si.add_class('particle_properties', class_name='FieldParticleProperty', name=name,
                             write=i.params['write_interp_particle_prop_to_tracks_file'],
                             vector_dim = i.get_number_components(),
                             time_varying=True, dtype='float64', initial_value=0.)
        pass

    def update_readers(self, time_sec):

        self.reader.update(time_sec)

    def update_tidal_stranding_status(self, time_sec, alive):
        i = self.tidal_stranding
        i.timed_update(self.reader.grid, time_sec, alive)

    def setup_time_step(self, time_sec, xq, active):

        # set buffer index from this time and next inside stepinfo
        # get next two buffer time steps around the given time in reader ring buffer
        # plus global time step locations and time ftactions od timre step and put results in interpolators step info numpy structure
        info = self.info
        grid =self.reader.grid
        info['current_hydro_model_step'], info['current_buffer_steps'], info['fractional_time_steps'] = self.reader._time_step_and_buffer_offsets(time_sec)
        part_prop = si.class_roles.particle_properties
        reader = self.reader
        # find hori cell
        sel_fix = self.reader.interpolator.find_hori_cell(xq, active)

        sel_outside_open = part_prop['cell_search_status'].find_subset_where(sel_fix, 'eq', si.cell_search_status_flags.hit_open_boundary,
                                                                        out=self.get_partID_subset_buffer('B2'))
        if sel_outside_open.size > 0:
            self._fix_those_outside_open_boundary(sel_outside_open)

        # outside domain but not an open boundary,
        sel_outside_domain = part_prop['cell_search_status'].find_subset_where(sel_fix, 'eq',
                                                                        si.cell_search_status_flags.hit_domain_boundary,
                                                                        out=self.get_partID_subset_buffer('B2'))
        self._move_back(sel_outside_domain)

        if si.settings.block_dry_cells:
            sel_hit_dry = part_prop['cell_search_status'].find_subset_where(sel_fix, 'eq',
                                                                si.cell_search_status_flags.hit_dry_cell,
                                                                out=self.get_partID_subset_buffer('B2'))
            self._apply_dry_cell_boundary_condition(sel_hit_dry)

        # move back bad coords, nan etc
        sel = part_prop['cell_search_status'].find_subset_where(sel_fix, 'eq', si.cell_search_status_flags.bad_coord, out=self.get_partID_subset_buffer('B2'))
        self._move_back(sel) # those still bad, eg nan etc

        # move back cell search failed
        sel = part_prop['cell_search_status'].find_subset_where(sel_fix, 'eq', si.cell_search_status_flags.failed,
                                                    out=self.get_partID_subset_buffer('B2'))
        self._move_back(sel)  # those still bad, eg nan etc

        if reader.info['is3D']:
            # find vertical cell
            info = self.info
            reader.interpolator.find_vertical_cell(self.reader.fields, xq, info['current_buffer_steps'], info['fractional_time_steps'], active)
            pass

    def _make_a_reader(self,reader_params):
        # build a readers
        reader = setup_reader.make_a_reader_from_params(reader_params, si.settings,  crumbs='')
        reader.initial_setup()
        reader.final_setup()

        # add request to load compulsory fields
        reader.params['load_fields'] = list(set(['water_velocity', 'tide', 'water_depth'] + reader.params['load_fields']))

        # tag field group as 3D etc
        add_info= {}
        for n in ['is3D', 'geographic_coords','has_A_Z_profile','has_open_boundary',
                  'has_bottom_stress','start_time','end_time','input_dir']:
            add_info[n] = reader.info[n]
        return reader, add_info
    def _apply_dry_cell_boundary_condition(self, sel_hit_dry):
        # dry cell boundary
        self._move_back(sel_hit_dry)

    def _fix_those_outside_open_boundary(self, sel_outside):
        # deal with open boundary if none
        if not self.info['use_open_boundary']:
            self._move_back(sel_outside) # outside and no open boundary so move back
        else:
            si.class_roles['particle_properties']['status'].set_values( si.particle_status_flags.outside_open_boundary, sel_outside)

    def _move_back(self, sel):
        # do move backs for blocked and bad
        part_prop = si.class_roles.particle_properties
        if sel.size > 0:
            part_prop['x'].copy('x_last_good', sel)  # move back location
            part_prop['n_cell'].copy('n_cell_last_good', sel)  # move back the cell
            part_prop['bc_coords'].copy('bc_coords_last_good', sel)  # move back the cell
            part_prop['status'].copy('status_last_good', sel)  # set status to last good status

        # debug_util.plot_walk_step(xq, si.core__class_roles.reader.grid, part_prop)

    def interp_field_at_particle_locations(self, field_name, active, output=None):

        # in place evaluation of field interpolation
        # interp reader field_name inplace to particle locations to same time and memory
        # output can optionally be redirected to another particle property name different from  reader's field_name
        # particle_prop_name
        info= self.info
        part_prop = si.class_roles.particle_properties
        if output is None:   output = part_prop[field_name].used_buffer() # over write current values

        field= self.reader.fields[field_name]
        self.reader.interpolator.interp_field(field,info['current_buffer_steps'], info['fractional_time_steps'], output, active)

    def interp_named_2D_scalar_fields_at_given_locations_and_time(self, field_name, x, n_cell,bc_coords, time_sec= None,hydro_model_gridID=None):
        # interp reader field_name at specfied locations,  not particle locations
        # used for getting tide and water depth at release locations give cell and bc_coords
        # todo smarter ways to do this special case using interploator class, not numba kernals?
        part_prop = si.class_roles.particle_properties
        info = self.info

        field_instance = self.reader.fields[field_name]
        # is no output name given particle property for output is same as hindcast field_name
        output = np.full((x.shape[0], field_instance.data.shape[3]), np.nan) if field_instance.data.shape[3] > 1 else np.full((x.shape[0],), np.nan)
        active = np.arange(x.shape[0])

        if time_sec is None:
            triangle_eval_interp.time_independent_2D_scalar_field(output, field_instance.data,
                                            self.reader.grid['triangles'],n_cell, bc_coords, active)
        else:
            current_hydro_model_step, current_buffer_steps, fractional_time_steps = self.reader._time_step_and_buffer_offsets(time_sec)
            triangle_eval_interp.time_dependent_2D_scalar_field(current_buffer_steps, fractional_time_steps, output,
                                      field_instance.data, self.reader.grid['triangles'], n_cell, bc_coords, active)
        return output

    def interp_named_3D_vector_fields_at_given_locations_and_time(
        self, field_name, x, n_cell, bc_coords, nz_cell, z_fraction, time_sec=None, hydro_model_gridID=None
    ):
        # interp reader field_name at specfied locations,  not particle locations

        field_instance = self.reader.fields[field_name]
        F_data = field_instance.data

        if F_data.shape[3] > 1:
            output = np.full((x.shape[0], F_data.shape[3]), np.nan)
        else:
            # I think this should never happen as it implied a scalar 3D field?
            # Was part of Ross' code, tho.
            # Throw error for for the moment
            raise ValueError("3D vector field should have 3 components")
            # output = np.full((x.shape[0],), np.nan)
        active = np.arange(x.shape[0])

        if time_sec is None:
            raise NotImplementedError("Time-independent interpolation of 3D fields is not yet implemented.")
        else:
            current_hydro_model_step, current_buffer_steps, fractional_time_steps = (
                self.reader._time_step_and_buffer_offsets(time_sec)
            )
            # if self.info["mode3D"] == 1:
            if True:
                # these have spatially uniform and static map of z levels
                triangle_eval_interp.time_dependent_3D_vector_field_data_in_all_layers(
                    n_buffer=current_buffer_steps,
                    fractional_time_steps=fractional_time_steps,
                    F_data=self.reader.fields[field_name].data,
                    triangles=self.reader.grid["triangles"],
                    n_cell=n_cell,
                    bc_coords=bc_coords,
                    nz_cell=nz_cell,
                    z_fraction=z_fraction,
                    F_out=output,
                    active=active,
                )
            else:
                raise NotImplementedError("This functionality is not yet implemented.")
                # triangle_eval_interp.time_dependent_3D_vector_field_ragged_bottom(
                #     current_buffer_steps,
                #     fractional_time_steps,
                #     F_data,
                #     grid["triangles"],
                #     grid["bottom_interface_index"],
                #     part_prop["n_cell"].data,
                #     part_prop["bc_coords"].data,
                #     part_prop["nz_cell"].data,
                #     part_prop["z_fraction"].data,
                #     output,
                #     active,
                # )
        return output

    def update_dry_cell_values(self):
        # update 0-255 dry cell index for each interpolator
        grid = self.reader.grid
        info= self.info
        field_group_manager_util.update_dry_cell_index( grid['is_dry_cell_buffer'], grid['dry_cell_index'],
                                                   info['current_buffer_steps'], info['fractional_time_steps'])

        pass

    def screen_info(self):
        info = self.info
        s = f':H{info["current_hydro_model_step"]:04d}b{info["current_buffer_steps"][0]:02d}-{info["current_buffer_steps"][1]:02d}'
        return s
    def get_reader_info(self):
        d= dict(reader=self.reader.info)
        return d
    def are_points_inside_domain(self,x):
        # only primary/outer grid
        is_inside, part_data = self.reader.interpolator.are_points_inside_domain(x)
        n = x.shape[0]
        part_data['hydro_model_gridID'] = np.zeros((n,), dtype=np.int8)

        return is_inside, part_data

    def release_are_dry_cells(self, release_info):
        sel = self.reader.grid['dry_cell_index'][ release_info['n_cell']] > 128  # those dry
        return sel

    def hindcast_integrity(self):
        setup_reader._hindcast_integrity_checks(self.reader)

    def close(self):
        pass

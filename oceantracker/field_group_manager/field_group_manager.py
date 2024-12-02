from oceantracker.util.parameter_base_class import ParameterBaseClass

import numpy as np
from oceantracker.util import time_util, ncdf_util, json_util, cord_transforms
from oceantracker.field_group_manager.util import field_group_manager_util
from time import  perf_counter
from copy import deepcopy
from oceantracker.shared_info import shared_info as si
from  oceantracker.definitions import  node_types, cell_search_status_flags
from oceantracker.interpolator.util import  triangle_eval_interp
from oceantracker.reader._oceantracker_dataset import OceanTrackerDataSet

class FieldGroupManager(ParameterBaseClass):
    # class holding data in file and ability to spatially interpolate fields that it holds
    #   all the fields in a file and interpolation which belongs to the set of fields (rather than individual variable)
    # works with 2D or 3D  with appropriate interplotor
    known_field_types=['reader_field','custom_field']
    # todo distingish between hydro model reader fields and auxilary fields, eg waves from another reader
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.n_buffer = np.zeros((2, ), dtype=np.int32)

        info = self.info
        info['current_hydro_model_step']= 0
        info['fractional_time_steps']= np.zeros((2,), dtype=np.float64)
        info['current_buffer_steps'] = np.zeros((2,), dtype=np.int32)

    def initial_setup(self, reader_builder,  caller=None):
        ml = si.msg_logger
        info = self.info

        # build  primary. ie  velocity field, reader
        self._create_readers(reader_builder)
        reader = self.reader

        # add velocity reader to field group info
        info.update(reader.info)
        pass





    def build_readers(self):

        self.reader.build_reader()
        self.reader.write_hydro_model_grid()

        # todo add ancillary field readers here, eg waves

    def final_setup(self):
        ml = si.msg_logger
        info = self.info
        grid = self.reader.grid

        info['has_open_boundary_nodes'] = np.any(self.reader.grid['node_type'] == node_types.open_boundary)

        if 'use_open_boundary' not in info :
            # set info here if not preset by nested grids
            info['use_open_boundary'] = si.settings.use_open_boundary
        info['use_open_boundary'] = info['has_open_boundary_nodes'] and info['use_open_boundary']

        # set up dry cell adjacency space for triangle walk
        grid['adjacency_with_dry_edges'] = grid['adjacency'].copy()  # working space to add dry cell boundaries to

        self.reader.interpolator.final_setup()

        # add tidal stranding class
        i = si.add_class('tidal_stranding', {}, crumbs=f'field Group Manager>setup_hydro_fields> tidal standing setup ', caller=self)
        self.tidal_stranding = i

        pass
        if si.settings['display_grid_at_start'] and self.reader.info['gridID']==1:
            from matplotlib import pyplot as plt
            from plot_oceantracker.plot_utilities import display_grid
            display_grid(grid, 1)
            plt.show()


    def add_reader_field(self,name, params):
        r = self.reader
        r._add_a_reader_field(name, params)


    def add_custom_field(self,name, params, default_classID=None):
        r = self.reader
        i = si._class_importer.make_class_instance_from_params('fields',params, name=name,
                                            default_classID=default_classID)
        i.initial_setup(r.params['time_buffer_size'],r.info,r.fields, r.grid)
        r.fields[name] = i

        # add classes required by this class
        i.add_required_classes_and_settings(si.settings, r.reader_builder, self.msg_logger)



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
        i.start_update_timer()
        i.update(self.reader.grid, time_sec, alive)
        i.stop_update_timer()

    def setup_time_step(self, time_sec, xq, active):

        # set buffer index from this time and next inside stepinfo
        # get next two buffer time steps around the given time in reader ring buffer
        # plus global time step locations and time ftactions od timre step and put results in interpolators step info numpy structure
        info = self.info
        grid =self.reader.grid
        info['current_hydro_model_step'], info['current_buffer_steps'], info['fractional_time_steps']= self.reader._time_step_and_buffer_offsets(time_sec)
        part_prop = si.class_roles.particle_properties

        # find hori cell
        self.reader.interpolator.find_hori_cell(xq, active)

        # all those that need fixing, lateral boundaries and bad, ie cell_status < blocked_dry_cell
        sel_fix = part_prop['cell_search_status'].find_subset_where(active, 'lt', cell_search_status_flags.ok, out=self.get_partID_subset_buffer('B1'))

        sel_outside_open = part_prop['cell_search_status'].find_subset_where(sel_fix, 'eq', cell_search_status_flags.open_boundary_edge,
                                                                        out=self.get_partID_subset_buffer('B2'))
        if sel_outside_open.size > 0:
            self._fix_those_outside_open_boundary(sel_outside_open)

        # outside domain but not an open boundary,
        sel_outside_domain = part_prop['cell_search_status'].find_subset_where(sel_fix, 'eq',
                                                                        cell_search_status_flags.domain_edge,
                                                                        out=self.get_partID_subset_buffer('B2'))
        self._move_back(sel_outside_domain)

        if si.settings.block_dry_cells:
            sel_hit_dry = part_prop['cell_search_status'].find_subset_where(sel_fix, 'eq',
                                                                    cell_search_status_flags.dry_cell_edge,
                                                                    out=self.get_partID_subset_buffer('B2'))
            self._apply_dry_cell_boundary_condition(sel_hit_dry)

        # finally move back bad cell searches, nan etc
        sel = part_prop['cell_search_status'].find_subset_where(active, 'lt', cell_search_status_flags.dry_cell_edge, out=self.get_partID_subset_buffer('B2'))
        self._move_back(sel) # those still bad, eg nan etc

        if grid['is3D']:
            # find vertical cell
            info = self.info
            self.reader.interpolator.find_vertical_cell(self.reader.fields, xq, info['current_buffer_steps'], info['fractional_time_steps'], active)
            pass

    def _create_readers(self, reader_builder):
        # build a readers
        info = self.info

        self.reader = si._class_importer.make_class_instance_from_params('reader', reader_builder['params'],
                                   caller=self, crumbs=f'setup_hydro_fields> reader class ')
        reader = self.reader
        # first build data set
        dataset = OceanTrackerDataSet()
        dataset.build_dataset_from_catalog(reader_builder['catalog'])

        reader.initial_setup(reader_builder,dataset)
        # add request to load compulsory fields
        reader.params['load_fields'] = list(set(['water_velocity', 'tide', 'water_depth'] + reader.params['load_fields']))

        #todo add ancillary file readers below here


    def _apply_dry_cell_boundary_condition(self, sel_hit_dry):
        # dry cell boundary
        self._move_back(sel_hit_dry)

    def _fix_those_outside_open_boundary(self, sel_outside):
        part_prop = si.class_roles.particle_properties
        # deal with open boundary

        if self.info['use_open_boundary']:
            # dont move back
            part_prop['status'].set_values(si.particle_status_flags['outside_open_boundary'], sel_outside)
        else:
            # outside and no open boundary so move back
            self._move_back(sel_outside)

    def _move_back(self, sel):
        # do move backs for blocked and bad
        part_prop = si.class_roles.particle_properties
        if sel.size > 0:
            part_prop['x'].copy('x_last_good', sel)  # move back location
            part_prop['n_cell'].copy('n_cell_last_good', sel)  # move back the cell

        # debug_util.plot_walk_step(xq, si.core__class_roles.reader.grid, part_prop)


    #@function_profiler(__name__)
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

    def interp_named_2D_scalar_fields_at_given_locations_and_time(self, field_name, x, n_cell,bc_cords, time_sec= None,hydro_model_gridID=None):
        # interp reader field_name at specfied locations,  not particle locations
        # used for getting tide and water depth at release locations give cell and bc_cords
        #todo smarter ways to do this special case using interploator class, not numba kernals?
        part_prop = si.class_roles.particle_properties
        info = self.info

        field_instance = self.reader.fields[field_name]
        # is no output name given particle property for output is same as hindcast field_name
        output = np.full((x.shape[0], field_instance.data.shape[3]), np.nan) if field_instance.data.shape[3] > 1 else np.full((x.shape[0],), np.nan)
        active = np.arange(x.shape[0])

        if time_sec is None:
            triangle_eval_interp.time_independent_2D_scalar_field(output, field_instance.data,
                                            self.reader.grid['triangles'],n_cell, bc_cords, active)
        else:
            current_hydro_model_step, current_buffer_steps, fractional_time_steps = self.reader._time_step_and_buffer_offsets(time_sec)
            triangle_eval_interp.time_dependent_2D_scalar_field(current_buffer_steps, fractional_time_steps, output,
                                      field_instance.data, self.reader.grid['triangles'], n_cell, bc_cords, active)
        return output

    def update_dry_cell_values(self):
        # update 0-255 dry cell index for each interpolator
        grid = self.reader.grid
        info= self.info
        field_group_manager_util.update_dry_cell_index( grid['is_dry_cell_buffer'], grid['dry_cell_index'],
                                                   info['current_buffer_steps'], info['fractional_time_steps'])

        # dev copy adjacency matrix and include dry cell lateral boundaries
        #field_group_manager_util.update_dry_cell_adjacency(grid['adjacency'], grid['dry_cell_index'], grid['adjacency_with_dry_edges'])
        #print('xx', np.count_nonzero(grid['adjacency_with_dry_edges']==-3))
        pass

    def screen_info(self):
        info = self.info
        s = f':H{info["current_hydro_model_step"]:04d}b{info["current_buffer_steps"][0]:02d}-{info["current_buffer_steps"][1]:02d}'
        return s

    def are_points_inside_domain(self,x, include_dry_cells):
        # only primary/outer grid
        is_inside, part_data = self.reader.interpolator.are_points_inside_domain(x)
        n = x.shape[0]
        part_data['hydro_model_gridID'] = np.zeros((n,), dtype=np.int8)

        # get tide and water depth at particle locations

        if not include_dry_cells:
            # only  keep those in wet cells at this time
            is_inside = np.logical_and(is_inside , ~self.are_dry_cells(part_data['n_cell'] ))
        return is_inside, part_data

    def are_dry_cells(self, n_cell):
        sel = self.reader.grid['dry_cell_index'][n_cell] > 128  # those dry
        return sel
    
    def close(self):
        self.info.update(self.reader.info)


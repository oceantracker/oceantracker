import numpy as np
from os import  path
from time import perf_counter
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_base_class import  ParameterBaseClass
from oceantracker.util import output_util
from oceantracker.util.ncdf_util import NetCDFhandler
from datetime import datetime
from oceantracker.util.profiling_util import  function_profiler
from oceantracker.shared_info import shared_info as si
# class to write with, outline methods needed
# a non-writer, as all methods are None

class _BaseWriterV2(ParameterBaseClass):
    # particle property  write modes,   used to set when to write  properties to output, as well as if to calculate at all


    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params(
                        role_output_file_tag =  PVC('tracks', str),
                        update_interval =  PVC(None, float, min=0.01, units='sec', doc_str='the time in model seconds between writes (will be rounded to model time step)'),
                        output_step_count =  PVC(None,int,min=1,  obsolete=True,  doc_str='Use tracks_writer parameter "write_time_interval", hint=the time in seconds bewteen writes'),
                        turn_on_write_particle_properties_list =  PLC(None, str,doc_str= 'Change default write param of particle properties to write to tracks file, ie  tweak write flags individually'),
                        turn_off_write_particle_properties_list =  PLC(['water_velocity', 'velocity_modifier'], str,
                                    doc_str='Change default write param of particle properties to not write to tracks file, ie  tweak write flags individually'),
                        time_steps_per_per_file =  PVC(None, int,min=1, doc_str='Split track output into files with given number of time integer steps'),
                        write_dry_cell_flag =  PVC(False, bool, doc_str='Write dry cell flag to track output file for all cells, which can be used to show dry cells on plots, off by default to keep file size down '),
                        write_dry_cell_index=PVC(True, bool, obsolete=True,  doc_str='Replaced by write_dry_cell_flag, set to false by default'),
                        )
    def initial_setup(self):
        self.info['file_builder'] = {'dimensions': {}, 'attributes': {}, 'variables': {}}
        self.add_dimension('time_dim', None)
        self.add_dimension('vector2D', 2)
        self.add_dimension('vector3D', 3)

        self.info.update(output_file=[], total_time_steps_written=0,
                         time_steps_written_to_current_file=0, output_file_number = 0)
        self.nc = None

    def final_setup(self):
        params = self.params
        # set up write schedule
        if params['update_interval'] is None :
            params['update_interval'] = si.settings.time_step

        if si.settings['write_dry_cell_flag']:
            grid = si.core_class_roles.field_group_manager.reader.grid
            self.add_dimension('triangle_dim', grid['triangles'].shape[0])
            self.add_new_variable('dry_cell_index', ['time_dim','triangle_dim'], attributes={'description': 'Time series of grid dry index 0-255'},
                                  dtype=np.uint8, chunking=[si.settings.NCDF_time_chunk,grid['triangles'].shape[0]])
        self.add_scheduler('write_scheduler', interval=self.params['update_interval'], caller=self)
        pass

    def add_dimension(self, name, size):
        self.info['file_builder']['dimensions' ][name] ={'size': size}

    def add_global_attribute(self, name, value):
        self.info['file_builder']['attributes' ][name] = value

    def add_new_variable(self,name, dim_list,description=None, fill_value=None,
                         attributes=None, dtype=None, vector_dim=None, chunking=None):
        # add a varaible builder to use on output file sequence, as may split time steps
        if dtype is bool: dtype = np.int8
        if dtype is None: dtype=np.float64

        if vector_dim is not None and vector_dim > 1:
            vn = ['vector2D','vector3D']
            dim_list.append(vn[vector_dim-2])
            chunking.append(vector_dim)

        var={'dim_list': dim_list,
             'description' :description if description is not None else 'no description given',
             'attributes': attributes if attributes is not None else {},
             'chunks' : chunking,
             'fill_value': fill_value,
            'dtype' : np.int8  if dtype is bool else dtype}

        self.info['file_builder']['variables'][name] = var

    def open_file_if_needed(self):
        # opens file if file too large and returns true if it does
        info = self.info

        if self.nc is None or info['time_steps_written_to_current_file'] > si.settings.max_time_steps_per_file:
            fn = f'{si.run_info.output_file_base}_{self.params["role_output_file_tag"]}_{info["output_file_number"]:03d}.nc'
            if self.nc is not None:
                #print('xxID', self.nc.read_a_variable('particle_ID')[:10])
                self._close_file()
            self._open_file(fn)
            info["output_file_number"] += 1

    def _open_file(self, file_name):
        t0 = perf_counter()
        info = self.info
        info['time_steps_written_to_current_file'] = 0
        info['output_file'].append(file_name)

        self.add_global_attribute('file_created', datetime.now().isoformat())

        self.nc = NetCDFhandler(path.join(si.run_info.run_output_dir, file_name), 'w')
        nc = self.nc

        for name, item in self.info['file_builder']['dimensions'].items():
            nc.add_dimension(name, item['size'])

        # create variables
        for name, item in self.info['file_builder']['variables'].items():
            # check chunk size under 4GB
            if item['chunks'] is not None:
                c = np.asarray(item['chunks'],dtype=np.int64) # avoids float 32 over flow
                b = np.prod(c)*np.full((0,),0 ).astype(item['dtype']).itemsize # btypes in a chunk
                if float(b) >= 4.0e9 :
                    si.msg_logger.msg('Netcdf chunk size for variable "' + name + '" exceeds 4GB, chunks=' + str(c), error=True,
                                            hint='Reduce tracks_writer param NCDF_time_chunk (will be slower), if many dead particles then use compact mode and manually set case_param particle_buffer_size to hold number alive at the same time', )
            #print('xx', name)
            nc.create_a_variable(name, item['dim_list'] , item['dtype'],  description=item['description'],  attributes=item['attributes'], chunksizes=item['chunks'],)

        # write status values to  file attributes
        output_util.add_particle_status_values_to_netcdf(nc)

       # note file opening and time to open file set up chucks and write first block
        si.msg_logger.progress_marker(f'Opened tracks output to : "{self.info["output_file"][-1]}"', start_time=t0)
        pass

    def _close_file(self):
        nc = self.nc

        # add all global attributes from builder
        for name, item in self.info['file_builder']['attributes'].items():
            nc.write_global_attribute(name, item)

        # info  properties only written at end
        nc.write_global_attribute('total_num_particles_released', si.core_class_roles.particle_group_manager.info['particles_released'])
        nc.write_global_attribute('time_steps_written', self.info['time_steps_written_to_current_file'])

        nc.close()
        self.nc = None

    def pre_time_step_write_book_keeping(self): pass

    def post_time_step_write_book_keeping(self):  pass

    def create_variable_to_write(self,name,first_dim_name,dim_len,**kwargs): pass

    def write_all_non_time_varing_part_properties(self, new_particleIDs):
    # to work in compact mode must write particle non-time varying  particle properties when released
    #  eg ID etc, releaseGroupID  etc

        writer = si.core_class_roles.tracks_writer
        if si.settings.write_tracks and new_particleIDs.shape[0] > 0:
            for name, prop in si.class_roles.particle_properties.items():
                # parameters are not time varying, so done at ends in retangular writes, or on culling particles
                if not prop.params['time_varying'] and prop.params['write']:
                    writer.write_non_time_varying_particle_prop(name, prop.data, new_particleIDs)

    #@function_profiler(__name__)
    def write_all_time_varying_prop_and_data(self):
        # write particle data at current time step, if none the a forced write
        # write time vary info , eg "time"
        self.start_update_timer()
        info = self.info
        #print('xx_ww1', self.info['time_steps_written_to_current_file'])
        self.pre_time_step_write_book_keeping()

        # write group data
        for name,i in si.class_roles.time_varying_info.items():
            if i.params['write']:
                self.write_time_varying_info(name, i)

        part_prop=si.class_roles.particle_properties
        for name,i in part_prop.items():
            if i.params['write'] and i.params['time_varying']:
                self.write_time_varying_particle_prop(name, i.data)

        if si.settings['write_dry_cell_flag']:
            # wont run if nested grids
            grid = si.core_class_roles.field_group_manager.reader.grid
            self.nc.file_handle.variables['dry_cell_index'][info['time_steps_written_to_current_file'], : ] = grid['dry_cell_index'].reshape(1,-1)

        self.post_time_step_write_book_keeping()
        #print('xx_ww2', self.info['time_particle_steps_written'])
        info['time_steps_written_to_current_file'] += 1 # time steps in current file
        info['total_time_steps_written']  += 1 # time steps written since the start
        self.stop_update_timer()

    def close(self):
        if si.settings.write_tracks and self.nc is not None:
            self._close_file()
            self.nc = None



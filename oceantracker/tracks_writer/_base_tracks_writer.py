import numpy as np
from os import  path
from time import perf_counter
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.parameter_base_class import  ParameterBaseClass
from oceantracker.util import basic_util
from oceantracker.util.ncdf_util import NetCDFhandler
from datetime import datetime
from oceantracker.util.profiling_util import  function_profiler
from oceantracker.shared_info import shared_info as si
# class to write with, outline methods needed
# a non-writer, as all methods are None

class _BaseWriter(ParameterBaseClass):
    # particle property  write modes,   used to set when to write  properties to output, as well as if to calculate at all
    def add_required_classes_and_settings(self,**kwargs):
        # dev holds last time step written to file, to allow filling values after this when reading into rectangular form
        si.add_class('particle_properties', name='last_written_time_steps_written', class_name='ManuallyUpdatedParticleProperty',
                     write=False, dtype='int32', time_varying=False,
                     initial_value=0, caller=self, crumbs='track writer, part prop')
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params(
                        role_output_file_tag =  PVC('tracks', str),
                        update_interval =  PVC(3600., float, min=1, units='sec', doc_str='the time in model seconds between writes (will be rounded to model time step)'),
                        output_step_count =  PVC(None,int,min=1,  obsolete=True,  doc_str='Use tracks_writer parameter "write_time_interval", hint=the time in seconds bewteen writes'),
                        turn_on_write_particle_properties_list =  PLC(None, str,doc_str= 'Change default write param of particle properties to write to tracks file, ie  tweak write flags individually'),
                        turn_off_write_particle_properties_list =  PLC(['water_velocity', 'velocity_modifier'], str,
                                    doc_str='Change default write param of particle properties to not write to tracks file, ie  tweak write flags individually'),
                        time_steps_per_per_file =  PVC(None, int,min=1, doc_str='Split track output into files with given number of time integer steps'),
                        write_dry_cell_flag =  PVC(False, bool, doc_str='Write dry cell flag to track output file for all cells, which can be used to show dry cells on plots, off by default to keep file size down '),
                        write_dry_cell_index=PVC(True, bool, obsolete=True,  doc_str='Replaced by write_dry_cell_flag, set to false by default'),
                        )
        self.info.update(output_file= [], total_time_steps_written = 0)


        self.info['variables_to_write'] = dict(time_varying_part_prop=[], non_time_varying_part_prop=[], time_varying_info=[])

        self.nc = None

    def initial_setup(self):
        pass

    def final_setup(self):
        params = self.params
        # set up write schedule
        self.add_scheduler('write_scheduler', interval= params['update_interval'], caller=self)
        pass

    def open_file_if_needed(self):
        params = self.params
        info = self.info

        n_file = len(info['output_file']) # files written so far

        if self.nc is None or (self.params['time_steps_per_per_file'] is not None and  info['time_steps_written_to_current_file'] // params['time_steps_per_per_file'] > 0):
            if self.nc is not None : self._close_file()
            fn = f'{si.run_info.output_file_base }_{params["role_output_file_tag"]}_{n_file:03d}'
            t0 = perf_counter()
            self._open_file(fn)
            # note file opening and time to open file set up chucks and write first block
            si.msg_logger.progress_marker(f'Opened tracks output and done written first time step in: "{self.info["output_file"][-1]}"', start_time=t0)


    def _open_file(self, file_name):
        info = self.info
        info['time_steps_written_to_current_file'] = 0
        info['output_file'].append(file_name + '.nc')

        self.nc = NetCDFhandler(path.join(si.run_info.root_output_dir, info['output_file'][-1]), 'w')
        nc = self.nc
        nc.create_attribute('file_created', datetime.now().isoformat())
        self.setup_file_vars(nc)
        # write non-time varing prop of those currently alive
        sel = self._select_part_to_write()
        part_prop = si.class_roles.particle_properties
        info['first_ID_in_file'] = part_prop['ID'].get_values(0)
        nc.create_attribute('first_ID_in_file', info['first_ID_in_file'])
        self.write_all_non_time_varing_part_properties(sel)
        
        pass

    def setup_file_vars(self, nc): basic_util.nopass('write muse have setup_file_vars method')

    def pre_time_step_write_book_keeping(self): pass

    def post_time_step_write_book_keeping(self):
        #self.estimate_open_file_size()
        pass

    def _select_part_to_write(self):
        part_prop = si.class_roles.particle_properties
        alive = part_prop['status'].compare_all_to_a_value('gt', si.particle_status_flags.dead,
                                                           out=self.get_partID_buffer('B1'))
        return alive
    def _close_file(self):
        nc = self.nc
        if nc is None: return
        # write properties only written at end
        nc.create_attribute('total_num_particles_released', si.core_class_roles.particle_group_manager.info['particles_released'])
        nc.create_attribute('time_steps_written', self.info['time_steps_written_to_current_file'])
        nc.close()

        self.nc = None

    def close(self):
        if self.nc is not None:
            self._close_file()



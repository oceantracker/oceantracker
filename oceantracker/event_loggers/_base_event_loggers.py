import os

import numpy as np
from numba  import njit
from copy import copy,deepcopy
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.ncdf_util import  NetCDFhandler
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC

class _BaseEventLogger(ParameterBaseClass):

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({'role_output_file_tag': PVC('event_logger',str),
                                 'write': PVC(True,bool),
                                 'chunk_size' : PVC(5000, int, min= 1),
                                 'particle_prop_to_write_list': PLC([ 'ID','x','IDpulse', 'IDrelease_group', 'user_release_groupID', 'status', 'age'],[str])})
    def check_requirements(self):

        msg_list = self.check_class_required_fields_list_properties_grid_vars_and_3D(required_props_list=['event_has_started_boolean'])
        return msg_list

    def initialize(self):
        si = self.shared_info
        buffer_size= si.particle_buffer_size

        # boolean buffer partile prop to recorded history of event having started (must be prop to be managed in compact mode)
        particle = si.classes['particle_group_manager']
        particle.create_particle_property('manual_update',dict(name='event_has_started_boolean',  initial_value=False, dtype=bool, write=False))

        # place to record which particles where events has just started or
        # just end based on changes in event_has_started_boolean to know which events to write
        self.event_has_started_IDbuffer = np.full((buffer_size,), -1, np.int32)
        self.event_has_ended_IDbuffer   = np.full((buffer_size,), -1, np.int32)

        self.time_steps_written = 0

    def find_events(self, event_is_happening_boolean):
        # find particles where event has just started or just ended, by comparing event_is_happening_boolean and recorded history in self.event_has_started_boolean
        # event_is_happening_boolean must be the size of the number of working particles in the buffer, which is a view if larger buffer
        # eg. based on number of particles in buffer
        # returns particle indices where event has started and ended

        event_has_started_boolean = self.shared_info.classes['particle_properties']['event_has_started_boolean'].data

        IDs_event_began, IDs_event_ended = self._find_particles_where_event_has_started_or_ended_numba(
                                                        event_has_started_boolean,
                                                        event_is_happening_boolean,
                                                        self.event_has_started_IDbuffer,
                                                        self.event_has_ended_IDbuffer)
        return  IDs_event_began, IDs_event_ended

    def set_up_output_file(self,addition_prop_to_write = None):
        # set up netcdf-file variables with open dimension
        si= self.shared_info
        part_prop = si.classes['particle_properties']
        params = self.params
        info= self.info

        if not params['write']: return

        # set up unique list of props to write
        info['prop_to_write'] = list(set(deepcopy(params['particle_prop_to_write_list']) + addition_prop_to_write))

        info['output_file'] = si.output_file_base + '_events_%03.0f' % (self.info['instanceID']  + 1) + '.nc'
        self.nc = NetCDFhandler(os.path.join(si.run_output_dir, info['output_file']), 'w')

        self.nc.add_a_Dimension('event', dim_size=None) # open dim

        chunk = si.particle_buffer_size if params['chunk_size'] is None else params['chunk_size']

        vec_dims= ['oneD','twoD','threeD' ]
        for n, d in enumerate(vec_dims): self.nc.add_a_Dimension(d, dim_size=n +1)

        self.nc.create_a_variable('event_flag', ['event'], {'notes': 'event strated =1, ended = -1'}, np.int8, chunksizes=[chunk])
        self.nc.create_a_variable('time', ['event'], {'notes': 'time in sec'}, np.float64,  chunksizes=[chunk])

        for prop_name in  info['prop_to_write']:
            pp = part_prop[prop_name]
            dims = ['event']
            cs =  [chunk]
            # adjust for vectors
            if pp.num_vector_dimensions()  > 0:
                dims +=  [vec_dims[pp.num_vector_dimensions() - 1]]
                cs +=  [pp.num_vector_dimensions()]

            self.nc.create_a_variable(prop_name, dims, {'notes': 'values when event started or ended'}, pp.get_dtype(), chunksizes= cs)

    def write_events(self,IDs_event_began, IDs_event_ended):
        # prop to write is list of particle prop to write beyond the standard ones, e.g.  ID of polygon each particle is inside, to note which polygon event is associated with
        si = self.shared_info
        part_prop= si.classes['particle_properties']

        time = si.classes['time_varying_info']['time'].get_values()

        for event_flag, IDs in zip([1,-1], [IDs_event_began, IDs_event_ended]):

            if IDs.shape[0]== 0 : continue

            file_index = self.time_steps_written + np.arange(IDs.shape[0])
            self.nc.file_handle.variables['event_flag'][file_index] = np.full_like(file_index, event_flag, dtype=np.int8)
            self.nc.file_handle.variables['time'][file_index] = np.full_like(file_index, time)

            # write part prop at time of event
            for prop_name in self.info['prop_to_write']:
                values = part_prop[prop_name].get_values(IDs)
                self.nc.file_handle.variables[prop_name][file_index, ...] = values

            self.time_steps_written += file_index.shape[0]

    @staticmethod
    @njit
    def _find_particles_where_event_has_started_or_ended_numba(event_has_started, event_happening, event_has_started_IDbuffer, event_has_ended_IDbuffer):
        # loops over all particle in buffer to return views of event_has_started_IDbuffer
        # and event_has_ended_IDbuffer, which are indices of particles where event has just started or just ended

        n_started  = 0
        n_finished = 0

        for n in range(event_happening.shape[0]):

            if event_happening[n] and (not event_has_started[n]):
                # a new event is starting, ie one which hasn't yet started
                event_has_started[n] = True
                event_has_started_IDbuffer[n_started] = n
                n_started += 1

            elif event_has_started[n] and (not event_happening[n])  :
                #  a started event has ended, ie no longer happening
                event_has_started[n] = False
                event_has_ended_IDbuffer[n_finished] = n
                n_finished += 1

        # return views of IDs where event has started or ended
        return event_has_started_IDbuffer[:n_started], event_has_ended_IDbuffer[:n_finished]

    def close(self):
        if self.params['write']:  self.nc.close()
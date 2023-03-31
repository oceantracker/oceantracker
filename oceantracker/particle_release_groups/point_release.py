import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import time_util
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from itertools import count
from numba import njit
class PointRelease(ParameterBaseClass):
    # releases particles at fixed points, inside optional radius
    # add checks to see if points inside domain and dry if released in a radius
    #todo make a parent release base class

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({
                                 'points':          PVC([],'vector', is_required=True, doc_str='A N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array'),
                                 'release_radius':  PVC(0., float, min= 0., doc_str= 'Particles are released from random locations in circle of given radius around each point.'),
                                 'pulse_size' :     PVC(1, int, min=1, doc_str= 'Number of particles released in a single pulse, this number is released every release_interval.'),
                                 'release_interval':PVC(0., float, min =0., doc_str= 'Time interval between released pulses. To release at only one time use release_interval=0.'),
                                 'release_start_date': PVC(None, 'iso8601date', doc_str='Must be an ISO date as string eg. "2017-01-01T00:30:00" '),
                                   # to do add ability to release on set dates/times 'release_dates': PLC([], 'iso8601date'),
                                 'release_duration': PVC(None, float,min=0,
                                                    doc_str='Time in seconds particles are released for after they start being released, ie releases stop this time after first release.' ),
                                'release_end_date': PVC(None, 'iso8601date', doc_str='Date to stop releasing partices, ignored if release_duration give, must be an ISO date as string eg. "2017-01-01T00:30:00" '),
                                'maximum_age': PVC(None,float,min=1.,
                                                    doc_str='Particles older than this time in seconds are killed off and removed from computation.'),
                                 'user_release_groupID' : PVC(0,int, doc_str= 'User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.'),
                                 'user_release_group_name' : PVC(None,str,doc_str= 'User given name/label to attached to this release groups to make it easier to distinguish.'),
                                 'allow_release_in_dry_cells': PVC(False, bool,
                                              doc_str='Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide.'),
                                 'z_range': PLC([],[float, int], min_length=2, doc_str='z range = [zmin, zmax] to randomly release in 3D, overrides any given release z value'),
                                  #Todo implement release group particle with different parameters, eg { 'oxygen' : {'decay_rate: 0.01, 'initial_value': 5.}
                                'max_cycles_to_find_release_points': PVC(50, int, min=50, doc_str='Maximum number of cycles to search for acceptable release points, ie. inside domain, polygon etc '),

                                'user_particle_property_parameters':{}, #  dictionary of items with keys of particle_properties,
                                                                            # each a dictionary of parameters for that property
                                                                            # eg { 'oxygen' : {'decay_rate: 0.01, 'initial_value': 5.}}
                                 })
        self.class_doc(description= 'Release particles at 1 or more given locations. Pulse_size particles are released every release_interval. All these particles are tagged as a single release_group.')


    def initialize(self):
        # must be called after unpack_x0
        # tidy up parameters to make them numpy arrays with first dimension equal to number of locations

        info=self.info
        info['points'] =   np.array(self.params['points']).astype(np.float64)

        info['number_released'] = 0 # count of particles released in this group
        info['pulse_count'] = 0

    def set_up_release_times(self, n):
        # get release times based on release_start_date, duration
        params = self.params
        info = self.info
        si = self.shared_info

        hindcast_start = si.classes['reader'].info['first_date']
        hindcast_end  = si.classes['reader'].info['last_date']
        hindcast_duration =  si.classes['reader'].info['duration']

        self.info['release_info'] ={'first_release_date': None, 'last_release_date':None,
                                    'last_date_alive':None,
                      'estimated_number_released' : 0,
                       'release_schedule_dates': None, 'index_of_next_release' : 0}
        # short cut
        release_info =self.info['release_info']

        if params['release_start_date'] is None:
        # no user start date so use  model runs' start date
            release_info['first_release_time'] = hindcast_start if not si.backtracking else hindcast_end
        else:
            # user given start date
            release_info['first_release_time'] = params['release_start_date']

        # now check if start in range
        if not hindcast_start <= release_info['first_release_time'] <= hindcast_end:
            si.msg_logger.msg('Release group= ' + str(n + 1) + ', name= ' + self.params['name'] + ',  parameter release_start_time is ' +
                                    str(release_info['first_release_time'])
                              + '  is outside hindcast range ' + str(hindcast_start)
                                    + ' to ' + str(hindcast_end), warning=True)
        # get max age of particles
        if params['maximum_age'] is None:
            max_age = time_util.float_sec_to_time_delta(1.0E20)
        else:
            max_age=  time_util.float_sec_to_time_delta(abs(params['maximum_age']))

        # world out release times
        if params['release_interval'] == 0.:
            release_times = np.asarray([release_info['first_release_time']])
        elif not si.backtracking:
            if self.params['release_duration'] is not None:
                t1 = release_info['first_release_time'] +  time_util.float_sec_to_time_delta(self.params['release_duration'])
            elif self.params['release_end_date'] is not None:
                t1 = self.params['release_end_date']
            else:
                t1 = hindcast_end
            release_times = np.arange(release_info['first_release_time'],t1,
                                      time_util.float_sec_to_time_delta(abs(params['release_interval'])))
            release_info['last_time_alive'] = min(hindcast_end, release_times[-1] +  max_age)

        else:
            # backtracking
            if self.params['release_duration'] is not None:
                t1 = release_info['first_release_time'] - time_util.float_sec_to_time_delta(self.params['release_duration'])
            elif self.params['release_end_date'] is not None:
                t1 = self.params['release_end_date']
            else:
                t1 = hindcast_start
            release_times = np.arange(release_info['first_release_time'], t1,
                                      time_util.float_sec_to_time_delta(-abs(params['release_interval'])))
            release_info['last_time_alive'] = max(hindcast_start, release_times[-1] - max_age)

        release_info['release_schedule_times'] = release_times
        release_info['last_release_time'] = release_times[-1] # ensure it matches release times
        release_info['estimated_number_released'] =  self.estimated_total_number_released(release_info)

    def estimated_total_number_released(self,release_info):
        info = self.info

        npart= self.params['pulse_size'] *  release_info['release_schedule_times'].size * info['points'].shape[0]
        npart = int( npart+ max(10,.03*npart)) # add 3% more safety  margin
        return npart

    def release_locations(self):
        # set up full set of release locations inside  polygons
        si = self.shared_info
        grid = si.classes['reader'].grid
        grid_time_buffers = si.classes['reader'].grid_time_buffers
        info= self.info

        n_required = self.get_number_required()

        x0           = np.full((0, info['points'].shape[1]), 0.)
        n_cell_guess = np.full((0,), 0, dtype=np.int32)
        count = 0
        n_found = 0

        while x0.shape[0] < n_required:
            # get 2D release candidates
            x = self.get_release_location_candidates()
            x, n_cell = self.check_potential_release_locations_in_bounds(x)

            if x.shape[0] > 0:
                x, n_cell = self.filter_release_points(x, n_cell)
                # if any ok then add to list
                n_found += x.shape[0]
                x0          = np.concatenate((x0, x), axis =0)
                n_cell_guess= np.concatenate((n_cell_guess, n_cell))

            # allow max_cycles_to_find_release_points cycles to find points
            count += 1
            if count > self.params["max_cycles_to_find_release_points"]: break

        if n_found < n_required:
            si.msg_logger.msg('Release, only found ' + str(n_found) + ' of ' + str(n_required) + ' required points inside domain after 50 cycles',warning=True,
                           hint=f'Maybe, release points outside the domain?, or hydro-model grid and release points use different coordinate systems?? or increase parameter  max_cycles_to_find_release_points, current value = {self.params["max_cycles_to_find_release_points"]:3}' )
            n_required = n_found #

        # trim initial location and cell  to required number
        x0 = x0[:n_required, :]
        n_cell_guess = n_cell_guess [:n_required]

        n = x0.shape[0]
        IDrelease_group = self.info['instanceID']
        IDpulse = info['pulse_count']
        info['pulse_count'] += 1
        user_release_groupID = self.params['user_release_groupID']

        info['number_released'] += n  # count number released in this group

        if si.hydro_model_is3D and (len(self.params['z_range']) > 0 or x0.shape[1] < 3):

            if len(self.params['z_range']) == 0:  self.params['z_range']= [-1.0E30,1.0E30]

            z = self.get_z_release_in_depth_range(np.asarray(self.params['z_range']), n_cell_guess,
                                            grid_time_buffers['zlevel'], grid['bottom_cell_index'] , grid['triangles'],
                                            si.classes['field_group_manager'].get_current_reader_time_buffer_index())
            x0 = np.hstack((x0[:, :2], z))

        return x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess

    @staticmethod
    @njit()
    def get_z_release_in_depth_range(z_range, ncell, zlevel, bottom_cell_index ,triangles, nb):
        # get release in range of top and bottom
        nx = ncell.shape[0]

        zr =  np.full((2,),0.)
        z = np.full((nx,1),0.)

        for n in range(nx):
            # get mean depth of triangle by summing
            ztop, zbot = 0., 0.
            for m in range(3):
                node = triangles[ncell[n],m]
                ztop += zlevel[nb, node, -1]
                zbot += zlevel[nb, node, bottom_cell_index[node]]

            zr[0] = max(zbot/3., z_range[0])
            zr[1] = min(ztop/3., z_range[1])

            z[n] = np.random.uniform(zr[0], zr[1], size=1)

        return z




    def get_number_required(self):
        return self.params['pulse_size']*self.info['points'].shape[0]

    def get_release_location_candidates(self):
        si = self.shared_info
        x = np.repeat(self.info['points'], self.params['pulse_size'], axis=0)

        if self.params['release_radius']> 0.:
            rr = abs(float(self.params['release_radius']))
            n = x.shape[0]
            rr = np.repeat(rr, n, axis=0)
            r = np.random.random((n,)) * rr * np.exp(1.0j * np.random.random((n,)) * 2.0 * np.pi)
            r = r.reshape((-1, 1))
            x[:, :2] += np.hstack((np.real(r), np.imag(r)))

        return x


    def filter_release_points(self, xy, n_cell):
        # user can filter release points by inheritance of this class and overriding this method
        return xy, n_cell

    def check_potential_release_locations_in_bounds(self, x):
        si= self.shared_info
        grid_time_buffers = si.classes['reader'].grid_time_buffers
        # use KD tree to find points those outside model domain

        sel, n_cell = si.classes['interpolator'].are_points_inside_domain(x[:,:2])

        # keep those inside domain
        x = x[sel, :]
        n_cell = n_cell[sel]

        # add keep only those in wet cells at this time
        if not self.params['allow_release_in_dry_cells']:
            sel =grid_time_buffers['dry_cell_index'][n_cell] < 128 # those wet
            x = x[sel, :]
            n_cell = n_cell[sel]

        return x, n_cell


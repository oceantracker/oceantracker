import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import time_util
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from itertools import count
from numba import njit
class PointRelease(ParameterBaseClass):
    # releases particles at fixed points, inside optional radius
    # todo add checks to see if points inside domain and dry if released in a radius


    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({
                                 'points':          PVC([],'vector', is_required=True, doc_str='A N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array'),
                                 'release_radius':  PVC(0., float, min= 0., doc_str= 'Particles are released from random locations in circle of given radius around each point.'),
                                 'pulse_size' :     PVC(1, int, min=1, doc_str= 'Number of particles released in a single pulse, this number is released every release_interval.'),
                                 'release_interval':PVC(0., float, min =0., doc_str= 'Time interval between released pulses. To release at only one time use release_interval=0.'),
                                 'release_start_date': PVC(None, 'iso8601date'),
                                 'release_duration': PVC(1.0e32, float,min=0,
                                                    doc_str='Time in seconds particles are released for after they start being released, ie releases stop this time after first release.' ),
                                 'maximum_age': PVC(1.0e32,float,min=1.,
                                                    doc_str='Particles older than this time in seconds are killed off and removed from computation.'),
                                 'user_release_groupID' : PVC(0,int, doc_str= 'User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.'),
                                 'user_release_group_name' : PVC(None,str,doc_str= 'User given name/label to attached to this release groups to make it easier to distinguish.'),
                                 'allow_release_in_dry_cells': PVC(False, bool,
                                              doc_str='Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide.'),
                                 'z_range': PLC([],[float, int], min_length=2, doc_str='z range = [zmin, zmax] to randomly release in 3D, overrides any given release z value'),
                                  #Todo implement release group particle with different parameters, eg { 'oxygen' : {'decay_rate: 0.01, 'initial_value': 5.}
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

        hindcast_start = si.classes['reader'].get_first_time_in_hindcast()
        hindcast_end = si.classes['reader'].get_last_time_in_hindcast()
        hindcast_duration = abs(hindcast_end-hindcast_start)

        release_info={'first_release_date': None, 'last_release_date':None,'last_date_alive':None,
                      'estimated_number_released' : 0,
                      'first_release_time': None, 'last_release_time':None, 'last_time_alive':None,
                      'release_schedule_times': None, 'index_of_next_release' : 0}



        if params['release_start_date'] is None:
        # no user start date so use  model runs' start date
            release_info['first_release_time'] = hindcast_start if not si.backtracking else hindcast_end
        else:
            # user given start date
            d0 = time_util.date_from_iso8601str(params['release_start_date'], err_msg='Particle Group ,   Parameter release_start_date not valid iso date string')
            release_info['first_release_time'] = time_util.date_to_seconds(d0)

        # now check if start in range
        if not hindcast_start <= release_info['first_release_time'] <= hindcast_end:
            si.case_log.write_msg('Release group= ' + str(n+1) + ',  parameter release_start_time is ' +
                               time_util.seconds_to_iso8601str(release_info['first_release_time']) + '  is outside hindcast range ' + time_util.seconds_to_iso8601str(hindcast_start)
                               + ' to ' + time_util.seconds_to_iso8601str(hindcast_end), warning=True)

        # todo allow a list of release dates for the group, eg elif params['release_dates']:
        if params['release_interval'] == 0:
            release_times = np.asarray([release_info['first_release_time']])
        else:
            release_times = release_info['first_release_time'] +  si.model_direction*np.arange(0,hindcast_duration, abs(params['release_interval']))

        # clip release times to be within hindcast range
        sel = np.logical_and(release_times >= hindcast_start, release_times <= hindcast_end)
        release_times = release_times[sel]

        if release_times.shape[0] == 0:
              return release_info

        # clip release times to be less than that of release duration
        sel = (release_times - release_times[0])*si.model_direction <= self.params['release_duration']
        release_info['release_schedule_times'] = release_times[sel]

        release_info['last_release_time'] = release_times[-1]
        release_info['last_time_alive'] = release_times[-1] + self.params['maximum_age']*si.model_direction


        # get life span of group in forward time order
        if si.backtracking:
            release_info['last_time_alive']  = max(release_info['last_time_alive'], hindcast_start)
        else:
            release_info['last_time_alive'] = min(release_info['last_time_alive'], hindcast_end)

        # convert dates to time for easier debugging
        release_info['first_release_date']= time_util.seconds_to_iso8601str(release_info['first_release_time'])
        release_info['last_release_date'] = time_util.seconds_to_iso8601str(release_info['last_release_time'])
        release_info['last_date_alive'] = time_util.seconds_to_iso8601str(release_info['last_time_alive'])

        release_info['estimated_number_released'] =  self.estimated_total_number_released(release_info)

        release_info.update(self.params)
        self.info['release_info']= release_info
        return release_info

    def estimated_total_number_released(self,release_info):
        info = self.info
        if release_info['release_schedule_times'] is None:
            return 0
        else:
            npart= self.params['pulse_size'] *  release_info['release_schedule_times'].shape[0] * info['points'].shape[0]
            npart = int( npart+ max(10,.03*npart)) # add 3% more safety  margin
            return npart

    def release_locations(self):
        # set up full set of release locations inside  polygons
        si = self.shared_info
        grid = si.classes['reader'].grid
        info= self.info

        n_required = self.get_number_required()

        x0           = np.full((0, info['points'].shape[1]), 0.)
        n_cell_guess = np.full((0,), 0)
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

            # allow 50 cycles to find points
            count += 1
            if count > 50: break

        if n_found < n_required:
            si.case_log.write_warning('Release, only found ' + str(n_found) + ' of ' + str(n_required) + ' required points inside domain after 50 cycles')
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

        if si.hindcast_is3D and (len(self.params['z_range']) > 0 or x0.shape[1] < 3):

            if len(self.params['z_range']) == 0:  self.params['z_range']= [-1.0E30,1.0E30]

            z = self.get_z_release_in_depth_range(np.asarray(self.params['z_range']), n_cell_guess,
                                            grid['zlevel'], grid['bottom_cell_index'] , grid['triangles'],
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
        grid = si.classes['reader'].grid
        # use KD tree to find points those outside model domain

        sel, n_cell = si.classes['interpolator'].are_points_inside_domain(x[:,:2])

        # keep those inside domain
        x = x[sel, :]
        n_cell = n_cell[sel]

        # add keep only those in wet cells, crudely this is those not in dry cell at this and the next time step
        if not self.params['allow_release_in_dry_cells']:
            sel =grid['dry_cell_index'][n_cell] < 128
            x = x[sel, :]
            n_cell = n_cell[sel]

        return x, n_cell


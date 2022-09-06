import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import time_util
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from itertools import count
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
                                 'z_range': PLC([],[float], min_length=2, doc_str='z range = [zmin, zmax] to randomly release in 3D, overrides any given release z value'),
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
        info['points'] = self.initial_check_of_points()

        info['number_released'] = 0 # count of particles released in this group
        info['pulse_count'] = 0

    def initial_check_of_points(self):
        si= self.shared_info

        x0 = np.array(self.params['points']).astype(np.float64)

        if si.hindcast_is3D:
            if x0.shape[1] != 3:
                # add 3rd dim to x0
                x0=np.hstack( (x0, np.zeros((x0.shape[0],1))))
                si.case_log.write_warning('x0 is 2D for 3D hindcast, releasing at depth 0.0')
        else:
            # 2D run,  ensure x0 is 2D
            x0= x0[:,:2]

        return x0

    def set_up_release_times(self, n):
        # get release times based on release_start_date, duration
        params = self.params
        info = self.info
        si = self.shared_info

        hindcast_start = si.classes['reader'].get_first_time_in_hindcast()
        hindcast_end = si.classes['reader'].get_last_time_in_hindcast()
        hindcast_duration = abs(hindcast_end-hindcast_start)


        if params['release_start_date'] is None:
        # no user start date so use  model runs' start date
            t_start = hindcast_start if not si.backtracking else hindcast_end
        else:
            # user given start date
            d0 = time_util.date_from_iso8601str(params['release_start_date'], err_msg='Particle Group ,   Parameter release_start_date not valid iso date string')
            t_start = time_util.date_to_seconds(d0)


        # now check if start in range
        if not hindcast_start <= t_start <= hindcast_end:
            si.case_log.write_msg('Release group= ' + str(n+1) + ',  parameter release_start_time is ' +
                               time_util.seconds_to_iso8601str(t_start) + '  is outside hindcast range ' + time_util.seconds_to_iso8601str(hindcast_start)
                               + ' to ' + time_util.seconds_to_iso8601str(hindcast_end), warning=True)

        if params['release_interval'] == 0:
            release_times = np.asarray([t_start])
            # todo allow a list of release dates, eg elif params['release_dates']:
        else:
            release_times = t_start + si.model_direction*np.arange(0, min(hindcast_duration,self.params['release_duration']) , abs(params['release_interval']))

        # get life span of group in forward time order
        if si.backtracking:
            time_last_particle_alive = max(release_times[-1] - self.params['maximum_age'], hindcast_start)
            info['group_life_span']  = [time_last_particle_alive,release_times[0]]
        else:
            time_last_particle_alive = min(release_times[-1] + self.params['maximum_age'], hindcast_end)
            info['group_life_span'] = [release_times[0], time_last_particle_alive ]

        # now clip release times to be within hindcast and those with less than release_duration
        sel = np.logical_and(release_times >= hindcast_start, release_times  <= hindcast_end)

        if np.any(sel):
            info['release_schedule_times']= release_times[sel]
        else:
            si.case_log.write_msg('Release group= ' + str(n + 1) + ',  no release times in date range of hind cast  ' + time_util.seconds_to_iso8601str(hindcast_start)
                                  + ' to ' + time_util.seconds_to_iso8601str(hindcast_end), warning=True)
            info['release_schedule_times'] = None
            info['group_life_span'] = [release_times[0], release_times[0]]

        info['index_of_next_release'] = 0 #


    def estimated_total_number_released(self):
        info = self.info
        if info['release_schedule_times'] is None:
            return 0
        else:
            npart= self.params['pulse_size'] *  info['release_schedule_times'].shape[0] * info['points'].shape[0]
            npart = int( npart+ max(10,.03*npart)) # add 3% more safety  margin
            return npart

    def release_locations(self):
        # set up full set of release locations inside  polygons
        si = self.shared_info
        info= self.info

        n_required = self.get_number_required()

        x0           = np.full((0, 3 if si.hindcast_is3D else 2), 0.)
        n_cell_guess = np.full((0,), 0)
        count = 0
        n_found = 0

        while x0.shape[0] < n_required:
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
        IDrelease_group = self.info['release_groupID']
        IDpulse = info['pulse_count']
        info['pulse_count'] += 1
        user_release_groupID = self.params['user_release_groupID']

        info['number_released'] += n  # count number released in this group

        return x0, IDrelease_group, IDpulse, user_release_groupID, n_cell_guess

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

        if si.hindcast_is3D  and len(self.params['z_range']) > 0:
            x[:,2] = np.random.uniform(self.params['z_range'][0],self.params['z_range'][1])

        return x


    def filter_release_points(self, xy, n_cell):
        # user can filter release points by inheritance of this class and overriding this method
        return xy, n_cell

    def check_potential_release_locations_in_bounds(self, x):
        si= self.shared_info
        # use KD tree to find points those outside model domain



        sel, n_cell = si.classes['interpolator'].are_points_inside_domain(x)


        # keep those inside domain
        x = x[sel, :]
        n_cell = n_cell[sel]

        # add keep only those in wet cells, crudely this is those not in dry cell at this and the next time step
        if not self.params['allow_release_in_dry_cells']:
            sel =si.grid['dry_cell_index'][n_cell] < 128
            x = x[sel, :]
            n_cell = n_cell[sel]

        return x, n_cell


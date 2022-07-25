import numpy as np
from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util import time_util
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from itertools import count
class PointRelease(ParameterBaseClass):
    # releases particles at fixed points, inside optional radius
    # todo add checks to see if points inside domain and in  depth range

    instanceID = 0

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({
                                 'points':          PVC([],'vector', is_required=True, doc_str='A N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array'),
                                 'release_radius':  PVC(0., float, min= 0., doc_str= 'Particles are released from random locations in circle of given radius around each point.'),
                                 'pulse_size' :     PVC(1, int, min=1, doc_str= 'Number of particles is a single pulse.'),
                                 'release_interval':PVC(0., float, min =0., doc_str= 'Time interval between released pulses.'),
                                 'release_start_date': PVC(None, 'iso8601date'),
                                 'release_duration': PVC(1.0e32, float,min=0,
                                                    doc_str='Time particles are released for after they start being released, ie releases stop this time after first release.' ),
                                 'maximum_age': PVC(1.0e32,float,min=1.,
                                                    doc_str='Particles older than this are killed off and removed from computation.'),
                                 'user_release_group_ID' : PVC(0,int, doc_str= 'User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.'),
                                 'user_release_group_name' : PVC(None,str,doc_str= 'User given name/label to attached to this release groups to make it easier to distinguish.'),
                                 #Todo implement release group particle parameters, eg { 'oxygen' : {'decay_rate: 0.01, 'initial_value': 5.}
                                 'user_particle_property_parameters':{}, #  dictionary of items with keys of particle_properties,
                                                                            # each a dictionary of parameters for that property
                                                                            # eg { 'oxygen' : {'decay_rate: 0.01, 'initial_value': 5.}}
                                 })
        self.class_doc(description= 'Release particles at 1 or more given locations. Pulse_size particles are released every release_interval. All these particles are tagged as a single release_group.')


    def initialize(self):
        # must be called after unpack_x0
        # tidy up parameters to make them numpy arrays with first dimension equal to number of locations

        info=self.info
        info['points'] = self.check_points()

        info['number_released'] = 0 # count of particles released in this group
        info['pulse_count'] = 0

    def check_points(self):
        si= self.shared_info

        x0 = np.array(self.params['points']).astype(np.float64)

        if si.hindcast_is3D and x0.shape[1] != 3 :
            x0=np.hstack( (x0, np.zeros((x0.shape[0],1))))
            si.case_log.write_warning('x0 is 2D for 3D hindcast, releasing at depth 0.0')

        return x0

    def set_up_release_times(self):
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
            # single user given date for start
            d0 = time_util.date_from_iso8601str(params['release_start_date'], err_msg='Particle Group ,   Parameter release_start_date not valid iso date string')
            t_start = time_util.date_to_seconds(d0)
            # now check in range
            if not hindcast_start <= t_start <= hindcast_end:
                si.case_log.write_msg('Release group parameter release_start_time is ' +
                                   time_util.seconds_to_iso8601str(t_start) + '  which is outside hindcast range ' + time_util.seconds_to_iso8601str(hindcast_start)
                                   + ' to ' + time_util.seconds_to_iso8601str(hindcast_end), warning=True)
                return  False

        if params['release_interval'] == 0:
            release_times = np.asarray([t_start])
        # todo allow a list of release dates, eg elif params['release_dates']:
        else:
            release_times = t_start + si.model_direction*np.arange(0, hindcast_duration, abs(params['release_interval']))

        # now clip release times to be within hincast and thoser with less than release_duration
        sel = np.logical_and(release_times >= hindcast_start, release_times  <= hindcast_end)
        sel = np.logical_and(sel, np.abs(release_times-release_times[0]) <= self.params['release_duration'])
        release_times= release_times[sel]

        # note start date info
        info['release_start_time'] = release_times[0]
        info['release_start_date'] = time_util.seconds_to_date(info['release_start_time'])
        info['release_duration'] = abs(release_times[-1] - release_times[0])

        if si.backtracking:
            info['group_life_span'] = [max(release_times[-1] - self.params['maximum_age'], hindcast_start), release_times[0]]
        else:
            info['group_life_span'] = [release_times[0], min(release_times[-1] + self.params['maximum_age'], hindcast_end)]

        info['group_life_span_dates'] = [time_util.seconds_to_iso8601str(info['group_life_span'][0]),time_util.seconds_to_iso8601str(info['group_life_span'][1])]

        if self.params['pulse_size'] < 1:
            si.case_log.write_warning('Pulse size param <  1 setting to 1')
            self.params['pulse_size'] = 1

        # record schedule
        self.release_schedule_times = release_times
        self.index_of_next_release = 0 # time of last release

        return True

    def estimated_total_number_released(self):
        npart= self.params['pulse_size'] *  self.release_schedule_times.shape[0] * self.info['points'].shape[0]
        npart = int( npart+ max(10,.03*npart)) # add 3% more safety  margin
        return npart

    def release_locations(self):
        # set up full set of release locations  x0ID, and groupID from sequence number
        si = self.shared_info
        info=self.info
        self.code_timer.start('Point release-release_locations')

        # expand for pulse size, use repeset to keep pulses together to improve kernal operation speeds
        x0 = np.repeat( self.info['points'], self.params['pulse_size'], axis=0)
        n = x0.shape[0]
        IDrelease_group = np.repeat(self.instanceID, n)  # is sequence number of origin particle group
        user_release_group_ID            = np.repeat(self.params['user_release_group_ID'], n)
        IDpulse         =  np.repeat(info['pulse_count'], n)
        info['pulse_count'] +=1

        # random release within horizontal circle at given depths
        rr= abs(float(self.params['release_radius']))
        if  rr> 0:
            rr = np.repeat(rr, n, axis=0)
            n = rr.shape[0]
            r = np.random.random((n,)) * rr * np.exp(1.0j * np.random.random((n,)) * 2.0 * np.pi)
            r = r.reshape((-1, 1))
            x0[:, :2] += np.hstack((np.real(r), np.imag(r)))

        n_cell_guess = si.classes['interpolator'].initial_cell_guess(x0[:, :2])

        self.info['number_released'] += IDrelease_group.shape[0] # count number released in this group

        self.code_timer.stop('Point release-release_locations')

        return x0, IDrelease_group, IDpulse, user_release_group_ID, n_cell_guess


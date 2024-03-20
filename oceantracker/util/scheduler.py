from inspect import signature
import numpy as np
from oceantracker.util import  time_util
class Scheduler(object):
    # set up event shedule based on times since 1/1/1970
    # rounds starts, times and intervals to model time steps,
    # uses times given, otherwise start and interval
    # all times in seconds
    def __init__(self, run_info,hindcast_info,
                 start=None, end=None, duration=None,
                 interval = None, times=None,cancel_when_done=True):

        self.interval_rounded_to_time_step = False
        self.times_rounded_to_time_step =  False
        self.start_time_outside_hydro_model_times = False

        self.cancel_when_done = cancel_when_done


        # deal with None and isodates
        if start is None: start = run_info['start_time']
        if type(start) is str: start = time_util.isostr_to_seconds(start)

        if end is None: end = run_info['end_time']
        if type(end) is str: end = time_util.isostr_to_seconds(end)

        dt = run_info['time_step']
        tol = 0.05

        if times is not None:
            # use times given
            # check if at model time steps
            n = (times - run_info['start_time'])/run_info['time_step']
            times_rounded = run_info['start_time'] + np.round(n) * run_info['time_step']

            if np.any(np.abs(times-times_rounded)/dt > tol * dt):
                self.times_rounded_to_time_step = True
            self.scheduled_times = times_rounded
        else:
            # make from start time and interval
            if start is None: start = run_info['start_time'] # start ast model sart
            if type(start) == str: start = time_util.isostr_to_seconds(start)

            n =(start- run_info['start_time'])/dt  # number of model steps since the start
            start_rounded = run_info['start_time'] + round(n)*dt
            if  abs(start_rounded-start)/dt > tol:
                self.times_rounded_to_time_step = True
            start = start_rounded

            if not ( hindcast_info['start_time'] <= start  <= hindcast_info['end_time']):
                self.start_time_outside_hydro_model_times = True

            # round interval
            if interval is None: interval = hindcast_info['time_step']
            interval = abs(interval)  # ensure positive
            rounded_interval = round(interval/dt)*dt
            if abs(interval-rounded_interval)/dt > tol:
                self.interval_rounded_to_time_step = True
            interval = rounded_interval

            # look at duration from end if given
            if duration is None:
                if end is None: end = run_info['end_time'] # start ast model sart
                if type(end) == str: end = time_util.isostr_to_seconds(end)
                duration = abs(end-start)

            # make even starting
            if interval < .1*dt:
                # if interval is zero
                interval = 0.
                self.scheduled_times= np.asarray([start])
            else:
                interval = max(interval, dt)
                self.scheduled_times = start + np.arange(0, abs(duration), interval)

        # make a task flag for each time step of the model run
        self.task_flag = np.full_like(run_info['times'],False, dtype=bool)
        nt_task = ((self.scheduled_times - run_info['start_time']) / run_info['time_step']).astype(np.int32)

        # now clip times to be within model start and end of run
        sel = np.logical_and(nt_task >= 0, nt_task < self.task_flag.size)
        self.task_flag[nt_task[sel]] = True

        # flag times steps scheduler is active, ie start to end
        self.active_flag = np.full_like(run_info['times'], False, dtype=bool)
        self.active_flag[nt_task[0]:nt_task[-1]+1] = True

        # record info
        self.info= dict(start_time=self.scheduled_times[0], interval=interval, end_time=self.scheduled_times[-1],
                        start_date=time_util.seconds_to_isostr(self.scheduled_times[0]),
                        end_date=time_util.seconds_to_isostr(self.scheduled_times[-1]),
                        number_scheduled_times = self.scheduled_times.size,
                        cancel_when_done=cancel_when_done
                        )

        pass

    def do_task(self, n_time_step):
        # check if task flag is set
        do_it = self.task_flag[n_time_step]

        if self.cancel_when_done and do_it:
            # ensure task is not repeated by another operation at the same time step
            self.task_flag[n_time_step] = False
        return do_it

    def cancel_task(self, n_time_step):
        # check if task flag is set
         self.task_flag[n_time_step] = False

    def see_task_flag(self, n_time_step):
        # returns if task is happening  without any cancellation of task when done
        return  self.task_flag[n_time_step]

    def is_active(self, n_time_step):
        # check if task is between start and end from active_flag is set
        return self.active_flag[n_time_step]
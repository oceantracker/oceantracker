from oceantracker.shared_info import shared_info as si
import numpy as np
from oceantracker.util import  time_util
class Scheduler(object):
    # set up event shedule based on times since 1/1/1970
    # rounds starts, times and intervals to model time steps,
    # uses times given, otherwise start and interval
    # all times in seconds
    def __init__(self,settings, run_info,
                 start=None, end=None, duration=None,
                 interval = None, times=None,cancel_when_done=True,
                 msg_logger=None,caller=None,crumbs=''):


        self.cancel_when_done = cancel_when_done
        md = run_info.model_direction
        dt = settings.time_step

        if times is None:
            # make from start time and interval
            times, interval = self._start_end_from_interval(settings,  run_info,start, end, duration, interval)
        else:
            # use times given, but round
            n = (times - run_info.start_time)/dt
            times = run_info.start_time + np.round(n) * dt
            times = md* np.sort(md*times) # ensure they are in right order for backwards/forwards
            interval = None

        # trim to fit inside the run
        sel = np.logical_and(times * md >= run_info.start_time * md, times * md <= run_info.end_time * md)
        self.scheduled_times = times[sel]

        # make a task flag for each time step of the model run
        self.task_flag = np.full_like(run_info.times,False, dtype=bool)
        nt_task = (np.abs(self.scheduled_times - run_info.start_time) / settings.time_step).astype(np.int32)
        self.task_flag[nt_task] = True

        # flag times steps scheduler is active, ie start to end
        self.active_flag = np.full_like(run_info.times, False, dtype=bool)
        if nt_task.size >0:
            self.active_flag[nt_task[0]:nt_task[-1]+1] = True
            duration = abs(self.scheduled_times[-1] - self.scheduled_times[0])
            start= self.scheduled_times[0]
            end=self.scheduled_times[-1]
        else:
            duration=None
            start=times[0]
            end= times[-1]
        # record info

        self.info= dict(start_time=start, interval=interval,
                        end_time=end,
                        duration = duration,
                        duration_str = time_util.seconds_to_pretty_duration_string(duration),
                        start_date=time_util.seconds_to_isostr(start),
                        end_date=time_util.seconds_to_isostr(end),
                        number_scheduled_times = self.scheduled_times.size,
                        cancel_when_done=cancel_when_done,
                        )
        i = self.info
        b = f'{12*" "} Scheduler{15*" "}Hindcast{14*" "}Run\n'
        b += f'Start- {i["start_date"]} | {time_util.seconds_to_isostr(run_info.hindcast_start_time)} | {time_util.seconds_to_isostr(run_info.times[0])}  \n'
        b += f'Ends - {i["end_date"]} | {time_util.seconds_to_isostr(run_info.hindcast_end_time)} | {time_util.seconds_to_isostr(run_info.times[-1])}]\n'
        b += f'{10*" "}interval = {i["interval"]}, backtracking={settings.backtracking}'
        i['bounds_table']= b

        if len(self.scheduled_times) == 0:
            msg_logger.msg('No times scheduled, as outside start and end times of run, see caller below',
                                hint=i['bounds_table'], caller=caller, error=True, crumbs=crumbs)

        if self.scheduled_times.size == 0:
            msg_logger.msg('No scheduled times within model run times',
                                hint=i['bounds_table'], caller=caller, error=True, crumbs=crumbs)

    def _start_end_from_interval(self,settings,run_info, start,end, duration, interval):

        md = run_info.model_direction
        dt = settings.time_step

        if start is None:
            start = run_info.hindcast_start_time if run_info.start_time is None else run_info.start_time
        else:
            # use given start rounded to time step
            n = (start - run_info.start_time) / dt  # number of model steps since the start
            start = run_info.start_time + round(n) *  dt

        if end is not None:
            # use end time instead to give duration
            duration = abs(end - start)

        elif duration is None:
            # duration is start to
            duration = abs(run_info.end_time-start)

        #trim within max duration
        duration = min(settings.max_run_duration, duration)

        # adjust end time to fit duration
        end = start + md * duration

        if interval is None:
            interval=  dt
        elif interval > 0.:
            # round interval to time step, but not less than one per time step
            interval=  max(round(interval/dt)*dt, dt)
        else:
            interval = 0.

        duration = abs(start-end)
        if interval ==0:
            # only one event
            times =np.asarray([start])
        else:
            times = start + md * np.arange(0,duration+settings.time_step,interval)

        return  times, interval

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
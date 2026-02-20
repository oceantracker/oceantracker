from oceantracker.shared_info import shared_info as si
import numpy as np
from oceantracker.util import  time_util
class Scheduler(object):
    # set up event schedule based on times since 1/1/1970
    # rounds starts, times and intervals to model time steps,
    # uses times given, otherwise start and interval
    # all times in seconds
    def __init__(self,si,name_scheduler,
                 start=None, end=None, duration=None,
                 interval = None, times=None,cancel_when_done=True,
                 msg_logger=None,caller=None):

        run_info = si.run_info
        settings = si.settings

        self.cancel_when_done = cancel_when_done
        self.name = name_scheduler
        md = run_info.model_direction
        dt = settings.time_step

        # The following is a bit more complicated because the scheduler needs to handle
        # cases correctly where we are running backward in time and or continue a 
        # previous run

        # To define the "earliest possible start" which differs for non-continued and continued runs
        if (run_info.continuing or run_info.restarting) and (start is None):
            # force scheduler to use start time of first/original run
            earliest_possible_start = si.saved_state_info['first_run_start_time'] 
        else: 
            # if it isn't a continuation/restart, 
            # then use given model start
            earliest_possible_start = run_info.start_time

        # Next we calculate the moments in time in which an operation is schedule
        if times is not None:
            # if they are manually defined, we just round them and are good to go
            n = (times - run_info.start_time)/dt
            times = run_info.start_time + np.round(n) * dt
            # and ensure they are in the right order for backwards/forwards
            times = md* np.sort(md*times) 
        else:
            # else we need to calculate them
            # by first getting the correct start time
            if start is None:
                # if it is not defined, we assume the user wants to start from 
                # the beginning of the model run
                start = earliest_possible_start
            else:
                # else we use their manually defined start
                start = start

            # next we need to figure out the end
            if end is not None:
                # if they defined it we just use it
                end = end
            elif duration is not None:
                # otherwise, we check if they defined a max duration, and use it to
                # calculate the end
                if duration > 100 * 365 * 24 * 3600:
                    # but first we double check that their value is not non-sensical
                    # (this should maybe go into the parameter checker?)
                    # check if user defined model duration is excessively long (>100 years)
                    # as it creates hard to interpret problems for the user otherwise if they
                    # i.e. accidentally used the wrong time unit
                    msg_logger.msg(
                        f'User defined scheduler duration is very long {duration/365/24/3600:.1f} > 100 years',
                        hint=f'Duration given {time_util.seconds_to_pretty_duration_string(duration)}',
                        caller=caller, strong_warning=True
                    )
                end = start + duration*md
            else: 
                # if neither end or duration is defined we assume that the user wants it
                # to happen for the full duration of the run
                end = run_info.end_time
            
            # 
            duration = np.abs(start - end)
            # trim within global max duration setting
            duration = min(settings.max_run_duration, duration)

            if interval is None:
                # if there is no interval provided, we assume it should happen on every
                # time step
                interval = dt
            elif interval > 0.:
                # if it is provieded (and non zero), we round interval to time step, but not less than one per time step
                interval=  max(round(interval/dt)*dt, dt)

            if interval == 0:
                # if the interval is zero, we assume it should only happen once, at the very start
                times =np.asarray([start])
            else:
                times = start + md * np.arange(0, duration+settings.time_step,interval)

        # check if any are scheduled, before trimming to allow for earlier actions of a continuation
        #todo add table of starts ends ?
        if times.size==0:
            msg_logger.msg( f'No actions are set for scheduler "{name_scheduler}"',
                hint=f'Time span of hindcast mismatched with start and end times of scheduler? Run continuation with actions starting in a future run?',
                caller=caller, strong_warning=True)

        # trim both before start and after
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

        if self.scheduled_times.size == 0:
            msg_logger.msg('No scheduled times within model run times',
                                hint=i['bounds_table'], caller=caller, strong_warning=True)
            

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
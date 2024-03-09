from inspect import signature
import numpy as np
class Scheduler(object):
    # set up event shedule based on times sincs 1/1/1970
    def __init__(self, run_info,
                 start=None, end=None,
                 interval = None, times=None, lags=None,
                 caller=None, msg_logger=None, crumbs=None):

        self.run_info = run_info
        self.start = start
        self.end = end
        self.interval = interval
        self.times = times
        self.lags = lags # times after start
        self.caller = caller
        self.msg_logger= msg_logger
        self.crumbs = crumbs

        pass
        self._create_schedule()

    def _create_schedule(self):
        ri = self.run_info
        if self.times is None:
            # use model start and end
            start = ri['start_time'] if self.start is None else self.start
            end = ri['end_time'] if self.end is None else self.end
        else:
            self.task_times = self.times

        if self.interval is None:
            pass # error
        else:
            n_steps = (end-start)/self.interval

        # time steps for each task
        nt_task = (self.task_times - ri['start_time']) / ri['model_time_step']

        if np.any(nt_task % 1 > 0.05):
            self.msg_logger.msg('Some times are not aliged with model time step',
                                warning=True,caller=self.caller)
        nt_task = nt_task.astype(np.int32)

        # clip out of model time range tasks
        nt_task = nt_task[nt_task < ri['times'].size]

        self.task = np.full_like(ri['times'],False, dtype=bool)
        # assign task flag
        self.task[nt_task] = True

from inspect import signature
import numpy as np
class Scheduler(object):
    # set up event shedule based on times sincs 1/1/1970
    def __init__(self, model_start_time, model_end_time, model_time_step,
                 start=None, end=None,
                 interval = None, times=None, lags=None,
                 caller=None, msg_logger=None, crumbs=None):

        self.model_start_time = model_start_time
        self.model_time_step = model_time_step
        self.model_end_time = model_end_time
        self.start = start
        self.end = end
        self.interval = interval
        self.times = times
        self.lags = lags # times after start
        self.caller = caller
        self.msg_logger= msg_logger
        self.crumbs = crumbs

        pass
        #self.create_schedule()

    def create_schedule(self):

        if self.times is None:
            # use model start and end
            start = self.model_start_time if self.start is None else self.start
            end = self.model_end_time if self.end is None else self.end
        else:
            start = self.times[0]
            end = self.times[-1]

        if self.interval is None:
            pass # error
        else:
            n_steps = (end-start)/self.interval
            self.task_times= np.linspace(start, end, self.interval)


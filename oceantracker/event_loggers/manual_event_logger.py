from  oceantracker.event_loggers._base_event_loggers import _BaseEventLogger
from oceantracker.util import basic_util

class ManualEventLogger(_BaseEventLogger):
    '''
    basic class to log events, can only be used through inheritance,  which must supply an update() method which calls
    this class's log_event() method to write events to the output file
    '''
    def update(self, n_time_step, time_sec, active=None):
        basic_util.nopass('ManualEventLogger can only be uses via inheritance, which must overwrite update() method which calls log_event() method')

    def log_event(self,sel, eventID: int):
        # write events for sel particle indicies to file tagged with the given event ID value
        pass


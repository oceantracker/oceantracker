from datetime import  datetime
import dateutil.parser
import math

import numpy as np
# deal with date time operations,

def seconds_to_datetime64(s):  return np.asarray(s).astype('datetime64[s]')


def seconds_to_isostr(s): return str(seconds_to_datetime64(s))

def datetime64_to_seconds(dt64):
    return dt64.astype(np.float64)

def isostr_to_seconds(s):
    # seconds since epoch of 1970-01-01
    # below works around date time assuming a computer local time zone if no timezone given
    d = dateutil.parser.isoparse(s)
    return np.datetime64(d).astype('datetime64[s]').astype(float)

def seconds_to_pretty_duration_string(s,seconds=True):
    td = np.timedelta64(int(np.round(s)),'s')
    days = td.astype('timedelta64[D]').astype(int)
    hours = (td.astype('timedelta64[h]') - days * 24).astype(int)
    minutes = (td.astype('timedelta64[m]') - days * 24 * 60 - hours * 60).astype(int)
    # Create the string representation
    s =  f"{days} days {hours} hrs {minutes} min"
    if seconds:
        seconds = (td.astype('timedelta64[s]') - days * 24 * 60 * 60 - hours * 60 * 60 - minutes*60).astype(int)
        s += f" {seconds} sec"

    return  s

def seconds_to_hours_mins_string(s):
    min = int(s / 60)
    hours =int(min /60)
    min  = int(min - hours * 60)
    return   f"{hours:1d} hrs {min:2d} min"

def seconds_to_pretty_str(s, seconds= True):
    fmt="%Y-%m-%d %H:%M"
    if seconds: fmt +=":%S"
    dt = datetime.utcfromtimestamp(s)
    return  dt.strftime(fmt)



def diff(date1,date2) :  return  (date1 - date2).total_seconds()


def iso8601_str(d)   :  return d.isoformat()

def  day_hms(x):
    # convert decimal seconds to days:  hms string
    days = math.floor(x/24/3600)
    x -= days*24*3600
    hours   =  math.floor(x/3600)
    x -= hours*3600
    minutes =  math.floor(x/60)

    return "%02.0f %02.0f:%02.0f" % (days, hours, minutes)

def get_regular_events(hindcast_info, backtracking, interval, msg_logger,
                       caller =None,
                       start=None, end=None,duration=None, crumbs=None ):
    # gets regularly spaced times within the hindcast span
    # and any start and end times, or a duration
    hi =hindcast_info
    h1, h2 =hi['start_time'], hi['end_time']
    model_dir = -1 if backtracking else 1
    interval = abs(interval)

    if backtracking:
        t1 = h2
        t2 = h1
    else:
        t1 = h1
        t2 = h2
    r =f'hydro-model range: {seconds_to_isostr(h1)} to {seconds_to_isostr(h2)}'
    if start is not None:
        s = isostr_to_seconds(start) if type(start) == str else start
        if not( h1 <= s <= h2):
            msg_logger.msg('Start time must be in the range of the hindcast',
                           hint= f'got {start}, ' + r,
                           fatal_error=True, exit_now=True, caller=caller,crumbs=crumbs)
        t1 = s # start at given time

    if end is not None:
        e = isostr_to_seconds(end) if type(end) == str else end
        if not (h1 <= e <= h2):
            msg_logger.msg('End time must be in the range of the hindcast',
                           hint=f'got {end}, ' + r,
                           fatal_error=True, exit_now=True, caller=caller,crumbs=crumbs)
        if  (e-t1)*model_dir < 0:
            msg_logger.msg('End time after/before start time if forward/backtracing',
                           hint=f'got start: {seconds_to_isostr(t1)}, end: {seconds_to_isostr(end)} ' ,
                           fatal_error=True, exit_now=True, caller=caller, crumbs=crumbs)
        t2 = end
    elif  duration is not None:
        # see if duration gives a shorter run
        tt = t1 + model_dir* abs(duration)
        if tt * model_dir < t2 * model_dir:
            t2 = tt

    duration = abs(t2-t1)
    if interval < 0.1:
        times = np.asarray([t1])
    else:
        times =  t1 + model_dir * np.arange(0,duration,interval)
    d = dict(start_time =times[0],end_time =times[-1], interval=interval,
             start_date = seconds_to_isostr(times[0]),
             end_date=seconds_to_isostr(times[-1]),
             times = times,
             dates = seconds_to_datetime64(times),
             duration = abs(times[-1] -times[0]),
            )
    return  d
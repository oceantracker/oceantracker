from datetime import datetime
import dateutil.parser
import math

import numpy as np
# deal with date time operations,

def seconds_to_datetime64(s):  return np.asarray(s).astype('datetime64[s]')

def seconds_to_isostr(s): return str(seconds_to_datetime64(s))

def datetime64_to_seconds(dt64):
    return dt64.astype('datetime64[s]').astype(np.float64)

def isostr_to_seconds(s):
    # seconds since epoch of 1970-01-01
    # below works around date time assuming a computer local time zone if no timezone given
    d = dateutil.parser.isoparse(s)
    return np.datetime64(d).astype('datetime64[s]').astype(float)

def seconds_to_pretty_duration_string(s,seconds=True):
    if s is None: return None
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


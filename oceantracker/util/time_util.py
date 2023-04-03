from datetime import  datetime, timedelta
import dateutil.parser
import math

import numpy as np
# deal with date time operations,

def seconds_to_datetime64(s):
    dt = datetime.utcfromtimestamp(s) # ignores time zone
    return np.datetime64(dt).astype('datetime64[s]')

def seconds_to_timedelta64(s): return np.asarray(s, dtype=np.float64).astype('timedelta64[s]')

def pretty_duration_string(td):
    #from timedelta64
    # Calculate days, hours, and minutes
    days = td.astype('timedelta64[D]').astype(int)
    hours = (td.astype('timedelta64[h]') - days * 24).astype(int)
    minutes = (td.astype('timedelta64[m]') - days * 24 * 60 - hours * 60).astype(int)

    # Create the string representation
    return  f"{days} days, {hours} hours, {minutes} minutes"

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
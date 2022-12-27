# utils for particle tracking
from  copy import deepcopy, copy
import time
import numpy as np
import platform
from psutil import  cpu_count, cpu_freq
from numba import  njit

class OceanTrackerDummyClass(object): pass

class BlockTimer(object):
    timer_dict = {}
    time_created = time.perf_counter()
    def start(self,name):
        # on first call create and set time zero
        if name not in self.timer_dict:
            self.timer_dict[name]={'time': 0.,'calls': 0,'time_first_call': 0.,'clock_started':0.}

        self.timer_dict[name]['clock_started'] = time.perf_counter()  # time zero as passing start

    def get_elapsed(self,name):
        return self.timer_dict[name]['time']

    def stop(self,name):
        d= self.timer_dict[name]
        d['time'] += time.perf_counter()- d['clock_started']
        d['calls'] += 1
        # record first_call timing
        if d['calls']==1: d['time_first_call'] =  d['time']

    def time_sorted_timings(self):
        # get times as list
        total_time = time.perf_counter() -  self.time_created
        times=[]
        all_text=[]
        for key,d in self.timer_dict.items():
            times.append(d['time'])
            txt = '%8.2fs' % d['time'] +  ' %3.0f%%' % (100*d['time']/total_time)
            txt += ' calls %05.0f: ' % d['calls'] + key
            txt += ',  (first call/remainder = %5.2fs' %   d['time_first_call'] + '/%5.2fs' % (d['time']-d['time_first_call'])
            all_text.append(txt)
        out=[]
        for  s in np.argsort(-abs(np.asarray(times))):
            out.append(all_text[s])
        return  out

    def report_string(self,ntabs=1, total_time = None):
        # make a timing mini report for this class
        tabs = ntabs*'\t'

        out= ''

        total_time = self.total_time() if total_time is None else total_time

        for key,d in self.timer_dict.items():
            out+=  tabs+'%8.2f' % d['time'] + ' sec :'
            out+=  ' - calls:%07.0f:- ' % d['calls']
            out += '% 6.1f%%' % (100.*d['time']/ total_time) +'   ' + key +'\n'

            # to do add nano sec per particle particle per time step


        return out

def deep_dict_update(d, d_updates):
    # recursively update dictionary tree d, ie a dictionary which may contain dictionaries with d_updates or listes of dictionaries
    # with corressponding key values in dictionary d_updates, d_updates may be a dictionary of dictionaries
    # note this is dumb, will just add new keys in any nested dictionary or change existing key in any nested dictionary based on d_update

    for key, item in d_updates.items():
        #print(key,type(item))
        if type(item) is dict:
            # if item itself is a dictionary
            if key not in  d: d[key]={}   # add and empty dictoary in d_updates not yet in d
            # recursively call update on this dictionary
            d[key] = deep_dict_update(d[key], item)

        elif type(item) is list and len(item)> 0 and type(item[0]) is dict:
            # case of a list of dictionaries
            if key not in d : d[key] = [] # empty list to fill with  dictionaries

            # list of dictionaries
            for n,d2 in enumerate(item):
                if n  >= len(d[key]) : d[key].append({})# add empty dictionary to d list to update
                d[key][n]= deep_dict_update(d[key][n], d2)
                #print(key,case, d2)
        else:
            # not a dictionary or list of dictionaries
            #print(key,item)
            d[key] = item
    return d



def get_computer_info():
    # can fail on some hardware??
    try:
        d={'OS':  platform.system() ,
           'OS Version' :platform.version(),
           'processor': platform.processor(),
            'CPUs_hardware':cpu_count(logical=False),
           'CPUs_logical': cpu_count(logical=True),
           'Freq_Mhz':  (cpu_freq().max/1000.)
           }
    except Exception as e:
        s= ' Failed to get computer info, error=' + str(e)
        d={'OS': s}

    return d

def nopass(msg=''):  raise Exception("Missing method, base method must be overwritten" +msg)



def atLeast_Nby1(y):
    # create a view of output with at least one vector component
    if y.ndim == 1:
        return  y.reshape((-1, 1))
    else:
        return y



@njit
def testNumbaRangeChecking():
    x= np.full((10,1),0.)
    x[x.shape[0]] = 1. # out of bounds test

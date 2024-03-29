from psutil import  cpu_count, cpu_freq
import platform
from oceantracker import  definitions

import  subprocess
from os import path


def get_computer_info():
    # can fail on some hardware??

    try:
        d={'name': platform.node(),
            'OS':  platform.system() ,
           'OS Version' :platform.version(),
           'processor': platform.processor(),
            'CPUs_hardware':cpu_count(logical=False),
           'CPUs_logical': cpu_count(logical=True),
           'Freq_Mhz':  (cpu_freq().max/1000.),
           }
    except Exception as e:
        s= ' Failed to get computer info, error=' + str(e)
        d={'OS': s}


    return d

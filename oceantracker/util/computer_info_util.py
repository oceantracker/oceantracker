from psutil import  cpu_count, cpu_freq , virtual_memory
import platform
from oceantracker import  definitions

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
           'memory_GB' : virtual_memory().total/10**9
           }
    except Exception as e:
        s= ' Failed to get computer info, error=' + str(e)
        d={'OS': s}

    return d

def get_git_commit():
    # oceantracker's own commit, found once at import from the package dir with git's stderr silenced,
    # running git here from the cwd printed "fatal: not a git repository" outside a repo
    # and recorded the hash of whatever repo the run was launched from
    return definitions.version['git_commit_hash']
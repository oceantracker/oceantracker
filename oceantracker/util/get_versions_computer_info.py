from psutil import  cpu_count, cpu_freq
import platform
from oceantracker import  common_info_default_param_dict_templates as common_info
from sys import version, version_info
import  subprocess
from os import path

def get_code_version():

    try:
        git_revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path.dirname(path.realpath(__file__))).decode().replace('\n', '')
    except:
        git_revision = 'unknown'

    d ={'major_version' : common_info.code_major_version,
        'version': common_info.code_version,
        'git_revision': git_revision,
        'python_version': version,
        'python_major_version': version_info.major,
        'python_minor_version': version_info.minor,
        'python_micro_version': version_info.micro,
        }

    return d


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

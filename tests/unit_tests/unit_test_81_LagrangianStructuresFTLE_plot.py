from os import path
from oceantracker.main import OceanTracker
from plot_oceantracker import plot_tracks
from read_oceantracker.python  import load_output_files
import numpy as np
from tests.unit_tests import test_definitions
from plot_oceantracker.plot_statistics import plot_LCS

# double gyre https://shaddenlab.berkeley.edu/uploads/LCS-tutorial/examples.html

def LCSplot(args):
    ot = OceanTracker()
    ot.add_class('reader', **test_definitions.demo_schisim)
    ot.settings(** test_definitions.set_output_loc(__file__))
    ot.settings(time_step=900)
    ot.add_class('integrated_model',class_name= 'dev_LagarangianStructuresFTLE2D',
                grid_size= [50, 100],
                grid_span = [6000,8000],
                grid_center = [1594000, 5484200],
                update_interval= 1800,
                lags= [3*3600],
                floating= True,
                )
    case_info_file_name= ot.run()

    LCS_data = load_output_files.load_LSC(case_info_file_name)

    plot_LCS(LCS_data)




    return None

def main(args):

    LCSplot(args)




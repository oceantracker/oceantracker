from os import path
from oceantracker.main import OceanTracker
from plot_oceantracker import plot_tracks

import numpy as np
from tests.unit_tests import test_definitions
from plot_oceantracker.plot_tracks import animate_particles

# double gyre https://shaddenlab.berkeley.edu/uploads/LCS-tutorial/examples.html

def LCS(args):
    ot = OceanTracker()
    dt =.25/4
    ot.add_class('reader', **test_definitions.reader_double_gyre)
    ot.settings(** test_definitions.set_output_loc(__file__))
    ot.settings(time_step=.25,screen_output_time_interval=1, include_dispersion=False)
    ot.add_class('integrated_model',class_name= 'dev_LagarangianStructuresFTLE2D',
                grid_size= [100, 200],
                write_intermediate_results= True,
                grid_span = [2,1],
                grid_center = [1,.5],
                update_interval= 0,
                lags= [15],
                floating= True,
                )
    case_info_file_name= ot.run()



    return None

def main(args):

    match args.variant:
        case 0:
            plot_tracks(args)
        case 1:
            #  now try integrated model
            LCS(args)




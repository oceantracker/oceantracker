from os import path
from oceantracker.main import OceanTracker
from plot_oceantracker import plot_tracks

import numpy as np
from tests.unit_tests import test_definitions
from plot_oceantracker.plot_tracks import animate_particles


def plot_tracks(args):
    ot = OceanTracker()
    dt = .05
    ot.settings(**test_definitions.set_output_loc(__file__))
    ot.settings(time_step=dt, screen_output_time_interval=1, include_dispersion=False)
    ot.add_class('reader', **test_definitions.reader_double_gyre)

    ot.add_class('tracks_writer', update_interval=dt)

    ot.add_class('release_groups', name='P1',class_name='GridRelease',
                 grid_size=[101, 201],
                 grid_span=[2, 1],
                 grid_center=[1, .5],
                 release_interval=0,
                 pulse_size=1)

    case_info_file = ot.run()

    tracks = test_definitions.read_tracks(case_info_file)

    movie_file1 = path.join(test_definitions.image_dir, 'decay_movie_frame.mp4') if args.save_plots else None

    animate_particles(tracks,show_release_points=False,
                                  show_grid=False, show_dry_cells=True, part_color_map='hot',
                                  # size_using_data=tracks['a_pollutant'],
                                  # colour_using_data=tracks['a_pollutant'],
                                  movie_file=movie_file1)
    return case_info_file

def LCS(args):
    ot = OceanTracker()
    dt =.1
    ot.add_class('reader', **test_definitions.reader_double_gyre)
    ot.settings(** test_definitions.set_output_loc(__file__))
    ot.settings(time_step=1,screen_output_time_interval=1, include_dispersion=False)
    ot.add_class('integrated_model',class_name= 'LagarangianCoherentStructuresFTLEheatmaps2D',
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




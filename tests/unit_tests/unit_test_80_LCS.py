from os import path
from oceantracker.main import OceanTracker
from plot_oceantracker import plot_tracks

import numpy as np
from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()

    ot.settings(time_step=1,display_grid_at_start=False, include_dispersion=False)
    ot.add_class('reader',  class_name ='oceantracker.reader.generic_stuctured_reader.GenericStructuredReader',
            input_dir= f'E:\H_Local_drive\ParticleTracking\hindcast_formats_examples\generic2D_structured_DoubleGyre',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
            file_mask = 'Double_gyre*.nc',
            dimension_map=dict(time='t', rows='y', cols='x'),
            grid_variable_map=dict(time='Time', x=['x_grid','y_grid']),
            field_variable_map =dict(water_depth='Depth',water_velocity=['U','V'], tide='Tide'),
            hydro_model_cords_in_lat_long = False
                 )   # the file mask of the hindcast files



    ot.add_class('release_groups', name ='P1',
                 points= [[.1,.5], [1.9, .5]],
                          release_interval= 0,
                        pulse_size= 1)



    case_info_file = ot.run()

    tracks= test_definitions.read_tracks(case_info_file)

    movie_file1= path.join(test_definitions.image_dir, 'decay_movie_frame.mp4') if args.save_plots else None

    plot_tracks.animate_particles(tracks,
                                  show_grid=True, show_dry_cells=True, part_color_map='hot',
                                  # size_using_data=tracks['a_pollutant'],
                                  # colour_using_data=tracks['a_pollutant'],
                                  movie_file=movie_file1)

    #plot_tracks.plot_utilities.animation_output(anim, 'output\test.mp4', fps=15, dpi=600, show=True)

    return case_info_file



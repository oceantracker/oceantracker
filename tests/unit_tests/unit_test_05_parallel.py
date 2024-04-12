from os import path
from oceantracker.main import OceanTracker
from plot_oceantracker import plot_tracks

import numpy as np
from tests.unit_tests import test_definitions

def main(args):
    ot = OceanTracker()
    ot.settings(**test_definitions.base_settings(__file__, args))
    ot.settings(time_step=120,processors=2)
    hm = test_definitions.hydro_model['demoSchism']
    ot.add_class('reader', **hm['reader'])

    # add releasess
    poly_points = [[1597682.1237, 5489972.7479],
                   [1598604.1667, 5490275.5488],
                   [1598886.4247, 5489464.0424],
                   [1597917.3387, 5489000],
                   [1597300, 5489000],
                   [1597682.1237, 5489972.7479]
                   ]
    ot.add_class('release_groups',
                  class_name= 'PolygonRelease',
                points= poly_points,  z_min=-1,   z_max= -1,
                release_interval=3603,
                start='2017-01-01T00:31:30', pulse_size= 10, case =0)

    ot.add_class('release_groups', name ='P1',case =1,
                 points= [[1594500, 5487000, -1],
                            [1594500, 5483000, -1],
                            [1598000, 5486100, -1] ],
                        release_interval= 3600,
                        pulse_size= 10)

    # add a decaying particle property,# with exponential decay based on age
    ot.add_class('particle_properties', **test_definitions.pp1) # add a new property to particle_properties role

    # add a gridded particle statistic to plot heat map
    ot.add_class('particle_statistics',**test_definitions.ps1)

    ot.add_class('dispersion', A_H= .2, A_V= 0.001)
    ot.add_class('resuspension', critical_friction_velocity=0.005)
    ot.add_class('velocity_modifiers', name ='fall_vel',
                    class_name= 'TerminalVelocity', value= -0.001 )

    case_info_file = ot.run()

    tracks= test_definitions.read_tracks(case_info_file[0])

    movie_file1= path.join(test_definitions.image_dir, 'decay_movie_frame.mp4') if args.save_plots else None

    anim= plot_tracks.animate_particles(tracks, axis_lims= test_definitions.ax,
                           show_grid=True, show_dry_cells=True, part_color_map='hot',
                           #size_using_data=tracks['a_pollutant'],
                           #colour_using_data=tracks['a_pollutant'],
                           movie_file=movie_file1)

    #plot_tracks.plot_utilities.animation_output(anim, 'output\test.mp4', fps=15, dpi=600, show=True)

    return case_info_file



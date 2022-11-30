from oceantracker.main import run
from oceantracker.post_processing.read_output_files import load_output_files
from oceantracker.util  import json_util
from oceantracker.util  import yaml_util
from os import path

import argparse
from oceantracker.post_processing.plotting import plot_tracks, plot_vertical_tracks, plot_statistics, plot_utilities
statistical_polygon_list = [
    {
        "user_polygon_name": "geesthacht",
        "points": [
            [
                585700.0,
                5921404.0
            ],
            [
                586412.0,
                5920095.0
            ],
            [
                594187.0,
                5917410.0
            ],
            [
                594346.0,
                5919695.0
            ],
            [
                587003.0,
                5922492.0
            ]
        ]
    },
    {
        "user_polygon_name": "neuengamme",
        "points": [
            [
                577905.0,
                5916461.0
            ],
            [
                582811.0,
                5915980.0
            ],
            [
                586412.0,
                5920095.0
            ],
            [
                585700.0,
                5921404.0
            ],
            [
                583464.0,
                5921191.0
            ],
            [
                578488.0,
                5917969.0
            ]
        ]
    },
    {
        "user_polygon_name": "kirchwerder",
        "points": [
            [
                577905.0,
                5916461.0
            ],
            [
                578488.0,
                5917969.0
            ],
            [
                574562.0,
                5927524.0
            ],
            [
                568765.0,
                5921992.0
            ]
        ]
    },
    {
        "user_polygon_name": "wilhelmsburg",
        "points": [
            [
                568765.0,
                5921992.0
            ],
            [
                574562.0,
                5927524.0
            ],
            [
                574027.0,
                5931853.0
            ],
            [
                569497.0,
                5933189.0
            ],
            [
                568607.0,
                5931906.0
            ],
            [
                568330.0,
                5931212.0
            ],
            [
                569596.0,
                5930624.0
            ],
            [
                569893.0,
                5930303.0
            ],
            [
                570051.0,
                5929822.0
            ],
            [
                569774.0,
                5929582.0
            ],
            [
                567993.0,
                5930437.0
            ],
            [
                564729.0,
                5924023.0
            ]
        ]
    },
    {
        "user_polygon_name": "harbor",
        "points": [
            [
                567380.0,
                5936476.0
            ],
            [
                554995.0,
                5934712.0
            ],
            [
                554600.0,
                5932895.0
            ],
            [
                564729.0,
                5924023.0
            ],
            [
                567993.0,
                5930437.0
            ],
            [
                569774.0,
                5929582.0
            ],
            [
                570051.0,
                5929822.0
            ],
            [
                569893.0,
                5930303.0
            ],
            [
                569596.0,
                5930624.0
            ],
            [
                568330.0,
                5931212.0
            ],
            [
                568607.0,
                5931906.0
            ],
            [
                569497.0,
                5933189.0
            ]
        ]
    },
    {
        "user_polygon_name": "schulau",
        "points": [
            [
                554600.0,
                5932895.0
            ],
            [
                554995.0,
                5934712.0
            ],
            [
                539772.0,
                5943332.0
            ],
            [
                535644.0,
                5936297.0
            ],
            [
                554909.0,
                5929980.0
            ],
            [
                555597.0,
                5931806.0
            ]
        ]
    },
    {
        "user_polygon_name": "stade",
        "points": [
            [
                535644.0,
                5936297.0
            ],
            [
                539772.0,
                5943332.0
            ],
            [
                533518.0,
                5959826.0
            ],
            [
                522176.0,
                5952740.0
            ]
        ]
    },
    {
        "user_polygon_name": "glückstadt",
        "points": [
            [
                522176.0,
                5952740.0
            ],
            [
                533518.0,
                5959826.0
            ],
            [
                525679.0,
                5969373.0
            ],
            [
                517339.0,
                5963566.0
            ]
        ]
    },
    {
        "user_polygon_name": "freiburg",
        "points": [
            [
                517339.0,
                5963566.0
            ],
            [
                525679.0,
                5969373.0
            ],
            [
                513670.0,
                5975376.0
            ],
            [
                513586.0,
                5965633.0
            ]
        ]
    },
    {
        "user_polygon_name": "brunsbüttel",
        "points": [
            [
                513586.0,
                5965633.0
            ],
            [
                513670.0,
                5975376.0
            ],
            [
                498742.0,
                5980888.0
            ],
            [
                491403.0,
                5958744.0
            ]
        ]
    },
    {
        "user_polygon_name": "ottendorf",
        "points": [
            [
                491403.0,
                5958744.0
            ],
            [
                498742.0,
                5980888.0
            ],
            [
                490569.0,
                5986990.0
            ],
            [
                471722.0,
                5956775.0
            ]
        ]
    },
    {
        "user_polygon_name": "cuxhafen",
        "points": [
            [
                471722.0,
                5956775.0
            ],
            [
                490569.0,
                5986990.0
            ],
            [
                494155.0,
                5985612.0
            ],
            [
                501411.0,
                5986005.0
            ],
            [
                501577.0,
                5991222.0
            ],
            [
                496073.0,
                6002441.0
            ],
            [
                485732.0,
                5999095.0
            ],
            [
                475475.0,
                5999390.0
            ],
            [
                468219.0,
                5995158.0
            ],
            [
                463883.0,
                5989056.0
            ],
            [
                460130.0,
                5982561.0
            ],
            [
                457461.0,
                5975475.0
            ],
            [
                459630.0,
                5968782.0
            ],
            [
                462799.0,
                5961499.0
            ]
        ]
    },
    {
        "user_polygon_name": "north_sea",
        "points": [
            [
                471722.0,
                5956775.0
            ],
            [
                462799.0,
                5961499.0
            ],
            [
                459630.0,
                5968782.0
            ],
            [
                457461.0,
                5975475.0
            ],
            [
                463883.0,
                5989056.0
            ],
            [
                468219.0,
                5995158.0
            ],
            [
                475475.0,
                5999390.0
            ],
            [
                485732.0,
                5999095.0
            ],
            [
                496073.0,
                6002441.0
            ],
            [
                480479.0,
                6011414.0
            ],
            [
                451123.0,
                6010595.0
            ],
            [
                438114.0,
                5987654.0
            ],
            [
                438114.0,
                5957612.0
            ],
            [
                468803.0,
                5943956.0
            ]
        ]
    }
]

if __name__ == '__main__':

    parser = argparse.ArgumentParser()


    parser.add_argument('-mode_debug', action='store_true')
    parser.add_argument('-noplots', action='store_true')
    parser.add_argument('-norun', action='store_true')

    args = parser.parse_args()
    input_dir= 'F:\\Hindcasts\\Hindcast_samples_tests\\LaurinGermany'

    x0 =[[502096, 5968781, -2], [485000, 5982000, -2],[470376, 5980287, -2],[ 536935,5940317, -2] ,[560849,5932934, -2],[448288.024467616, 5983779.777737856, -2]]
    #x0 = [[502096, 5968781, -2]]
    pulse_size = int(1000000/8) # 7 releases points/groups
    release_interval = 0
    pulse_size= 10

    release_interval = 3600
    case ={'run_params':{ 'particle_buffer_size': 120000,
                          'open_boundary_type':1,
                          'block_dry_cells': True,
            'duration': 7. * 24 * 3600,
                'write_tracks': True},
        'tracks_writer' : {'output_step_count': 15},
        'solver': { 'screen_output_step_count': 1,  'n_sub_steps': 30, 'RK_order': 2},
        'particle_release_groups': [{'points': x0,'pulse_size': pulse_size, 'release_interval': release_interval},
                                    {'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease',
                                     'points': statistical_polygon_list[1]['points'],'pulse_size': 10*pulse_size, 'release_interval': release_interval}],
        # 'dispersion': {'A_H': 0.2 ,'A_V': 0.001},
        'dispersion': {'A_H': 0.2 ,'A_V': 0.001,'class_name':'oceantracker.dispersion.random_walk_varyingAz.RandomWalkVaryingAZ'},
        'trajectory_modifiers': [{'class_name': 'oceantracker.trajectory_modifiers.resuspension.BasicResuspension',
                                       'critical_friction_velocity': .01},
            #{    "class_name": "oceantracker.trajectory_modifiers.split_particles.SplitParticles",  "splitting_interval": 180,  "split_status_greater_than": 'dead',   "probability_of_splitting": 0.01},
                                      ],

         'particle_properties': [{ 'class_name': 'oceantracker.particle_properties.total_water_depth.TotalWaterDepth'}],
         'particle_concentrations': [{'class_name': 'oceantracker.particle_concentrations.particle_concentrations.ParticleConcentrations2D'}],
         'fields' : [{'class_name': 'oceantracker.fields.friction_velocity.FrictionVelocity'},
                     {'class_name': 'oceantracker.fields.field_vertical_gradient.VerticalGradient','name_of_field': 'A_Z','name':'A_Z_vertical_gradient'}],

         'velocity_modifiers': [{'class_name': 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'mean': -0.00}],
        "particle_statistics": [
            {
                "class_name": "oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased",
                "calculation_interval": 100,
                "count_status_equal_to": 'moving',
                "particle_property_list": [],
                "polygon_list": statistical_polygon_list
            },
            {
                "class_name": "oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased",
                "calculation_interval": 100,
                "count_status_equal_to": 'stranded_by_tide',
                "particle_property_list": [],
                "polygon_list": statistical_polygon_list
            },
            {
                "class_name": "oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased",
                "calculation_interval": 100,
                "count_status_equal_to": 'on_bottom',
                "particle_property_list": [],
                "polygon_list": statistical_polygon_list
            }
        ]
    }

    params={ 'shared_params': {'output_file_base': 'Laurin_3d',
                                'debug': True,

                                'root_output_dir': 'F:\\OceanTrackerOuput\\Laurin',
                               'compact_mode': True
                               },
            'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',
                          'file_mask': 'schout_*.nc', 'input_dir': input_dir,
                      'hgrid_file_name': path.join(input_dir,'hgrid.gr3'),
                          'field_variables': { 'ECO_no3': 'ECO_no3','A_Z':'diffusivity'},# fields to track at particle locations
                       'field_variables_to_depth_average':['water_velocity']
                       },
               'case_list': [case]}


    if args.mode_debug: params['debug'] = True

    test = json_util.read_JSON('test_param_files/21_10_09_depth_accuracy_test_v01.json')
   # case['particle_release_groups'] = test['base_case_params']['particle_release_groups']
    json_util.write_JSON('test_param_files/LaurinTest.json',params)
    yaml_util.write_YAML('test_param_files/LaurinTest.yaml', params)

    if not args.norun:
        run_info_file, has_errors = run(params)
    else:
        run_info_file = path.join(params['shared_params']['root_output_dir'],params['shared_params']['output_file_base'],params['shared_params']['output_file_base']+'_runInfo.json' )


    if not args.noplots:
        caseInfoFile = load_output_files.get_case_info_file_from_run_file(run_info_file)

        m = load_output_files.load_stats_file(caseInfoFile, nsequence=1)
        track_data = load_output_files.load_particle_track_vars(caseInfoFile, var_list=['tide', 'water_depth'], fraction_to_read=.9)
        c = load_output_files.load_concentration_vars(caseInfoFile, var_list=['particle_concentration', 'C'])
        ax=[440000, 600000, 5910000,6010000]

        plot_tracks.animate_particles(track_data, axis_lims=ax, title='Laurin 3D Schism test', polygon_list_to_plot=m['polygon_list'],show_grid=True, interval=0,show_dry_cells=True)

        if 1 == 0:

            anim = plot_heat_maps.animate_concentrations(c, data_to_plot=c['particle_concentration'], logscale=True, shading=True,
                                                        axis_lims=ax, cmap='hot_r', vmin = 1.0e-7, vmax=.01,
                                                        title='SCHISIM-3D, 2D concentrations ')

            anim = plot_heat_maps.animate_concentrations(c, data_to_plot=c['particle_concentration'], logscale=True,shading=False,
                                                         axis_lims=ax, cmap='hot_r', vmin=1.0e-7, vmax=.01, back_ground_depth=False, title='SCHISIM-3D, 2D concentrations ')

            plot_vertical_tracks.plot_path_in_vertical_section(track_data, title='Laurin, sometimes resuspension_jump ', particleID=0)

            plot_vertical_tracks.plot_relative_height(track_data, title='Laurin, sometimes resuspension_jump ')
            plot_vertical_tracks.plot_relative_height(track_data, title='Laurin, sometimes resuspension_jump ', bottom=False)

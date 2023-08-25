from  oceantracker.main import run
import numpy as np
two_points= [[1594500, 5483000], [1598000, 5486100]]


poly_points=[[1597682.1237, 5489972.7479],
                        [1598604.1667, 5490275.5488],
                        [1598886.4247, 5489464.0424],
                        [1597917.3387, 5489000],
                        [1597300, 5489000], [1597682.1237, 5489972.7479]]

# case 50 schism basic
params=\
{'output_file_base' :'demo50_SCHISM_depthAver', 'debug': True,'time_step': 120,
 'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHISMSreaderNCDF',
                    'input_dir': '..\..\demos\demo_hindcast',
                             'file_mask': 'demoHindcastSchism3D.nc',
                     'field_variables':['water_temperature'],
                          },
        'dispersion': {'A_H': .2, 'A_V': 0.001},
        'release_groups': {
                    'P1':{'points': [[1595000, 5482600, -1],[1599000, 5486200, -1] ],
                                             'pulse_size': 10, 'release_interval': 3600,
                                            'allow_release_in_dry_cells': True},
                    'Poly1':    {'class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
                            'points': poly_points,
                            'pulse_size': 10, 'release_interval':  3600}
                },
            'particle_properties': {
                        'age_decay':{'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                                                  'decay_time_scale': 1. * 3600 * 24} },
            'event_loggers': {'inoutpoly':{'class_name': 'oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit',
                                                'particle_prop_to_write_list' : [ 'ID','x', 'IDrelease_group', 'status', 'age'],
                                                    'polygon_list': [{'user_polygon_name' : 'A','points': (np.asarray(poly_points) + np.asarray([-5000,0])).tolist()},
                                                                                                                                      ]
                                          }}
                }

run(params)
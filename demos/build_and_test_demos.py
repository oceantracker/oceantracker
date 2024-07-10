from os import path, mkdir, getcwd, chdir
import shutil
import subprocess
import argparse
import numpy as np
from oceantracker.util import json_util
from oceantracker.util import yaml_util
from copy import deepcopy


params =[]
two_points= [[1594500, 5483000], [1598000, 5486100]]


poly_points=[[1597682.1237, 5489972.7479],
                        [1598604.1667, 5490275.5488],
                        [1598886.4247, 5489464.0424],
                        [1597917.3387, 5489000],
                        [1597300, 5489000], [1597682.1237, 5489972.7479]
             ]
poly_points_large=[[1597682.1237, 5489972.7479],
                        [1598604.1667, 5490275.5488],
                        [1598886.4247, 5489464.0424],
                        [1597917.3387, 5487000],
                        [1597300, 5487000],
                       [1597682.1237, 5489972.7479]]

from oceantracker.reader.generic_unstructured_reader import GenericUnstructuredReader
demo_base_params={'output_file_base' : None,
  'add_date_to_run_output_dir': False,
    'NUMBA_cache_code': False,

   'time_step' : 900,
    'debug': True,
    'reader': {"class_name": 'oceantracker.reader.generic_unstructured_reader.GenericUnstructuredReader',
                'input_dir': '.',
                'file_mask': 'demoHindcast2D*.nc',
                'dimension_map': {'time': 'time', 'node': 'nodes'},
                'grid_variable_map'  : {'time': 'time_sec', 'x':['east','north'],  'triangles': 'tri'},
                'field_variable_map': {'water_velocity' : ['east_vel','north_vel'],'water_depth': 'depth','tide':'tide'},
                'time_buffer_size': 15,
                'isodate_of_hindcast_time_zero': '2020-06-01'},
    'user_note':'test of notes',
    #'numba_caching': False,
    'dispersion': {'A_H': .1},

    #'pre_processing':{'my_polygons':{'class_name': 'oceantracker.pre_processing.read_geomerty.ReadCoordinates',
    #                                 'file_name':'demo_hindcast/test.geojson',
    #                                 'type':'polygon'}},
    'tracks_writer': {'turn_on_write_particle_properties_list': ['n_cell'], 'write_dry_cell_flag': True},
    'release_groups': [{'name':'mypoints1', 'points': [[1594500, 5483000]], 'pulse_size': 200, 'release_interval': 0}],

    'particle_properties':[ {'name': 'Oxygen', 'class_name': 'AgeDecay', 'decay_time_scale': 1. * 3600 * 24,'initial_value' : 20.},
                            {'name':'distance_travelled','class_name': 'DistanceTravelled'},
                            {'name':'age_decay','class_name': 'AgeDecay', 'decay_time_scale': 1. * 3600 * 24},
                            {'name':'my_constant_prop','class_name': 'ParticleLoad','initial_value': 100}]
        }
p1= deepcopy(demo_base_params)
p1.update({'tracks_writer':{'time_steps_per_per_file':700, 'update_interval': 900*5 }}
                                )
p1.update({'output_file_base' :'demo01_plot_tracks' ,'backtracking': True,
                            'time_step': 600})
params.append(p1)

# demo 2 track animation
p2= deepcopy(demo_base_params)
p2['release_groups']=[ {'name':'point1','allow_release_in_dry_cells': True,
            'points': two_points, 'pulse_size': 10, 'release_interval': 3 * 3600},
     {'name':'poly1','class_name':'PolygonRelease',
            'points': deepcopy(poly_points),
            'pulse_size': 10, 'release_interval': 3 * 3600},
    {'name':'G1', 'class_name': 'GridRelease',
           'grid_size': [3, 4],
            'grid_span': [1000, 1000],
           'grid_center': [1592500, 5486000],
           'pulse_size': 2, 'release_interval': 3600}]


p2.update({'block_dry_cells': True,
        'tracks_writer':{'write_dry_cell_flag': True,
                                               }})
p2.update({'output_file_base' :'demo02_animation' ,'time_step': 10*60})
params.append(p2)


# demo 3
p3= deepcopy(demo_base_params)

p3['release_groups']= [{'name': 'myP1','points': [[1596000, 5486000]], 'pulse_size': 2000, 'release_interval': 7200, 'release_radius': 100.},
                       {'name':  'myP2','points': [[1596000, 5490000]], 'pulse_size': 2000, 'release_interval': 7200}]

p3['particle_statistics'] = [{'name':'gridstats1','class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                      'update_interval': 1800, 'particle_property_list': ['water_depth'],
                   'start': '2020-06-01 21:16:07',
                      'grid_size': [220, 221]},
                {'name':'polystats1','class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased',
                      'update_interval': 1800, 'particle_property_list': ['water_depth'],
                       'polygon_list':[ {'points':poly_points}]},]
p3.update({'particle_buffer_chunk_size': 20000, 'write_tracks': False,  'max_run_duration': 3 * 24 * 3600  })

p3.update({'output_file_base' :'demo03_heatmaps' })

params.append(p3)

# demo 4 age based heat maps
p4 = deepcopy(p3)
p4['particle_statistics'] = [
    { 'name':'age_grid','class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_ageBased',
             'update_interval': 1800, 'particle_property_list': ['water_depth'],
             'grid_size': [220, 221],
             'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.},
    { 'name':'age_poly','class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased',
             'update_interval': 1800, 'particle_property_list': ['water_depth', 'water_velocity'],
             'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.,
             'polygon_list': [{'points': poly_points} ] }]
p4.update({'output_file_base' :'demo04_ageBasedHeatmaps' })

params.append (p4)

# demo 5 parallel
base_case = deepcopy(p2)
del base_case['release_groups']
base_case.update({'output_file_base' :'demo05_parallel',
            'processors': 2,
          })
case_list=[]
for n in range(5):
    case_list.append({ 'release_groups': p2['release_groups']})
base_case['case_list'] = case_list
params.append(base_case)

# track animation with settlement on reef polygon
# demo 6
p6 = deepcopy(p2)

p6['release_groups']= [{'name': 'P1','points': [[1594500, 5482700], [1598000, 5486100], [1595500, 5489700]], 'pulse_size': 10, 'release_interval': 3 * 3600},
            {'name':'poly1','class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
             'points': deepcopy(poly_points),
             'pulse_size': 1, 'release_interval': 0}
            ]
p6['trajectory_modifiers']=[ {'name':'settle_in_polygon',
            'class_name': 'oceantracker.trajectory_modifiers.settle_in_polygon.SettleInPolygon',
             'polygon': {'points':  deepcopy(poly_points)},
             'probability_of_settlement': .1,
             'settlement_duration': 3.*3600}]
p6.update({'output_file_base' :'demo06_reefstranding' ,'backtracking': True})
p6['particle_statistics'] = [{'name': 'polystats1','class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased',
                    'update_interval': 1800, 'particle_property_list': ['water_depth'],
                'use_release_group_polygons': True,
                    'polygon_list':[ {'points':poly_points}]},]

params.append (p6)

# case 7 event logger
p7 = deepcopy(p2)

p7['release_groups']=[{'name': 'P1','points': [[1594500, 5490000], [1598000, 5488500]], 'pulse_size': 10, 'release_interval': 3 * 3600}]
p7['particle_properties'] =[{'name': 'age_decay','class_name': 'oceantracker.particle_properties.age_decay.AgeDecay','decay_time_scale': 1. * 3600 * 24}]

p7['event_loggers']=[{'name': 'in_out_poly','class_name': 'oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit',
                                                    'particle_prop_to_write_list' : [ 'ID','x', 'IDrelease_group', 'status', 'age'],
                                                        'polygon_list': [{'user_polygon_name' : 'A','points': (np.asarray(poly_points) + np.asarray([-5000,0])).tolist()},
                                                                         {'user_polygon_name' : 'B', 'points': poly_points_large}]
                                                                          }]
p7.update({'output_file_base' :'demo07_inside_polygon_events' })

params.append (p7)

# demo 8, particle splitting animation
p8 = deepcopy(p7)
p8['max_particles'] = 10**3

p8['release_groups']=[{'name':'P1','points': [[1594500, 5483500],[1594500, 5483500+3000]], 'pulse_size': 1, 'release_interval': 0}]

p8['trajectory_modifiers']=[{'name':'part_spliting',
           'class_name': 'oceantracker.trajectory_modifiers.split_particles.SplitParticles',
             'interval':6*3600,
                'statuses': ['moving'],
                    },
        {'name': 'part_culling','class_name': 'oceantracker.trajectory_modifiers.cull_particles.CullParticles',
             'interval': 6 * 3600,
             'statuses': ['moving'],
            'probability': .05}
                    ]

p8.update({'output_file_base' :'demo08_particle_splitting',  })
params.append (p8)


# test polygon release overlying land
p10= deepcopy(p2)
p10.update({'output_file_base' :'demo10_polygon_residence_demo',  })

p10['release_groups']= [ {'name': 'near_shore','class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
            'points': (np.asarray(poly_points) + np.asarray([[-3000.,-6500]])).tolist(),
            'pulse_size': 100, 'release_interval': 12 * 3600}]

p10['particle_statistics']= [{'name':'residentpoly' ,'class_name': 'ResidentInPolygon',
                  'name_of_polygon_release_group':'near_shore', 'update_interval': 1800}]


params.append(p10)



# case 50 schism basic
schsim_base_params=\
{'output_file_base' :'demo50_SCHISM_depthAver', 'debug': True,'time_step': 120,
            'NUMBA_cache_code': False,'use_A_Z_profile' : False,
            'regrid_z_to_uniform_sigma_levels': True,
                #'numba_caching': False,
        'reader': { #'class_name': 'oceantracker.reader.schism_reader.SCHISMreaderNCDF',
                    'input_dir': 'demo_hindcast',
                             'file_mask': 'demoHindcastSchism3D.nc',
                     'load_fields':['water_temperature']
                          },
        'dispersion': {'A_H': .2, 'A_V': 0.001},
        'release_groups':[ {'name': 'P1','points': [[1595000, 5482600, -1],[1599000, 5486200, -1] ],
                                             'pulse_size': 10, 'release_interval': 3600,
                                            'allow_release_in_dry_cells': True,
                          'start': '2017-01-01T01:30:00'},
                    {'name':'Poly1','class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
                            'points': poly_points,
                            'start': '2017-01-01T01:30:00',
                            'pulse_size': 10, 'release_interval':  3600}
                ],
            'particle_properties':[{'name': 'age_decay','class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                                                  'decay_time_scale': 1. * 3600 * 24} ],
            'event_loggers': [{'name':'inoutpoly','class_name': 'oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit',
                                                'particle_prop_to_write_list' : [ 'ID','x', 'IDrelease_group', 'status', 'age'],
                                                    'polygon_list': [{'user_polygon_name' : 'A','points': (np.asarray(poly_points) + np.asarray([-5000,0])).tolist()},
                                                                     {'user_polygon_name' : 'B', 'points': poly_points_large}
                                                                     ]
                                          }]
                }

s50 = deepcopy(schsim_base_params)
params.append (s50)

# schsim 3D
s56 = deepcopy(schsim_base_params)
# hydro start is '2017-01-01T00:30:00'
s56['release_groups']=[{'name': 'poly1','class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
                                    'points': poly_points,
                       'z_min': -1,
                        'z_max': -1,
                      'release_interval': 3603,
                        'start': '2017-01-01T00:31:30',
                        'pulse_size': 10, 'release_interval':  3660},
            {'name': 'P1', 'points': [[1594500, 5487000, -1],
                              [1594500, 5483000, -1],
                              [1598000, 5486100, -1]
                                ],
                'release_interval':  3600,
                'pulse_size': 10},]
s56['particle_statistics']= [ {'name':'grid1',   'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                      'update_interval': 3600, 'particle_property_list': ['water_depth'], 'status_min':'moving','z_min' :-2,
                      'grid_size': [120, 121]}]


s56['resuspension'] = {'critical_friction_velocity': .005}
#s56['resuspension'] = {'critical_friction_velocity': 1000.}
s56.update({'output_file_base' : 'demo56_SCHISM_3D_resupend_crtitical_friction_vel',
            })
s56['velocity_modifiers']= [ {'name': 'terminal_velocity','class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': -0.001}]

params.append (s56)

# schsim 3D, don't resupend lateral boundary test
s57 = deepcopy(s50)
s57.update(dict(use_A_Z_profile=True,use_random_seed= False))
s57.update({'output_file_base' : 'demo57_SCHISM_3D_lateralBoundaryTest'})
s57['dispersion'].update({'A_H':10,'A_V': 10})
s57['velocity_modifiers']= [{'name':'terminal_velocity','class_name' : 'TerminalVelocity', 'value': .000}
                            ]
s57['release_groups']=[{'name':'P1','points': [[1599750, 5485600, -1]], 'pulse_size': 20,
                      'release_interval': 3600, }   ]

params.append(s57)

# schsim 3D, vertical section
s58 = deepcopy(s56)
s58.update({'output_file_base' : 'demo58_bottomBounce', 'backtracking': False})
s58['dispersion'].update({'A_H': 0.1, 'A_V': .005})
bc = s58

bc['velocity_modifiers']=[{'name': 'terminal_velocity','class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': -0.002,'variance': 0.0002}]
bc['release_groups']= [{'name':'P11','pulse_size':10,'release_interval':0,
            'points': [[1593000., 5484000.+2000, -1]] ,
            'release_at_surface':True}] # only point release
params.append(s58)

# schsim 3D, vertical section  with critical friction velocity, A_z_profile
s59 = deepcopy(s58)
s59['use_A_Z_profile'] =True
s59.update({'output_file_base' : 'demo59_crit_shear_resupension', 'backtracking': False})
bc = s59
bc['velocity_modifiers']=[{'name':'terminal_velocity','class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': -0.002}]
s59['release_groups']=[{'name': 'P1','points': [[1594500, 5486000, -1]],  'pulse_size':1, 'release_interval':0}]
params.append(s59)

# decaying particles sized on c
s60 = deepcopy(schsim_base_params)
s60.update({'output_file_base' : 'demo60_SCHISM_3D_decaying_particle','time_step': 120})
s60['release_groups']=[{'name': 'P1','points': [[1594500, 5487000, -1], [1594500, 5483000, -1], [1598000, 5486100, -1]],
                      'pulse_size': 1, 'release_interval': 2.5*60, 'max_age': .2*24*3600}]
s60['particle_properties']= [{'name':'age_decay','class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                              'decay_time_scale':1*3600./0.14}]
s60.pop('event_loggers')
params.append(s60)

# triangle property/concetraaion plots particles sized on c
s61 = deepcopy(schsim_base_params)
s61.update({'max_run_duration': 15*24*3600.,'output_file_base': 'demo61_concentration_test'})
s61['write_tracks']= False
s61['particle_concentrations']= [{'name':'outfall_conc','class_name':'oceantracker.particle_concentrations.particle_concentrations.ParticleConcentrations2D',
                                                        'update_interval': 1800}]
for rg in s61['release_groups']:
    rg.update({'pulse_size': 1000, 'release_interval': 3600})

params.append(s61)


# test polygon release overlying land
p62 = deepcopy(schsim_base_params)
p62.update({'output_file_base' :'demo62_polygon_release_overlapping_land',  })
p62['release_groups']=[{'name':'Poly1','class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
         'points': (np.asarray(poly_points_large) + np.asarray([[0,-3000]])).tolist(),
         'pulse_size': 10, 'release_interval': 3*3600},
    {'name':'Poly2','class_name': 'oceantracker.release_groups.polygon_release_water_depth_range.PolygonReleaseWaterDepthRange',
            'water_depth_min': 30,
            'points': (np.asarray(poly_points_large) + np.asarray([[-3000, 0]])).tolist(),
            'pulse_size': 10, 'release_interval': 3 * 3600}]

params.append(p62)

p70 = deepcopy(schsim_base_params)
del p70['event_loggers']
p70.update({'output_file_base' :'demo70_LCS_test',
            #'NUMBA_cache_code': True,
            'time_step':600 })

p70['integrated_model']={'class_name': 'dev_LagarangianStructuresFTLE2D',
           'grid_size': [23, 30],
            'write_intermediate_results': True,
            'grid_span' : [ 10000, 9000],
           'grid_center': [1596500, 5486000],
            'release_interval': 705,
           'lags': [2*3600,3*3600],
            #'lags': [3*3600],
            'floating': True,
            }

params.append(p70)

# back tracking test
p90= deepcopy(p2)

p90.update({'max_run_duration': 2*24*3600.,'output_file_base': 'demo90forward',
            'include_dispersion':False,
            'backtracking': False,'debug': True,'time_step' :60 })
p90['reader']['time_buffer_size']=2  # test with  tiny buffer
p90['release_groups']= [{'name':'P1','pulse_size': 1, 'release_interval': 0,
           'points': [[1594500, 5486500], [1596500, 5489000], [1595000, 5483000] ]}]


p90['dispersion'].update({'A_H' : 0., 'A_V': 0.})

params.append(p90)

# test freewheeling when no particles
p91= deepcopy(p2) # has two points
p91.update({'output_file_base': 'demo91_free_running_gaps',
                             'time_step' :900 ,'backtracking': True})
p91['release_groups']={}
p91['release_groups']=[{'name':'r1','points':[two_points[1]],
                      'max_age':6*3600,
                     'release_interval':0,
                     'pulse_size' : 1,
                    'start':'2020-06-02T00:00:00' # start 1 day in 2020-06-02T21:16:07
                        }]
# 2020-06-01T05:16:07 to 2020-06-06T03:16:07
p91['release_groups'].append(dict(deepcopy(p91['release_groups'][0]),name='r2',start='2020-06-03T00:00:00'))
p91['release_groups'].append(dict(deepcopy(p91['release_groups'][0]),name='r3',start='2020-06-04T00:00:00'))
p91['release_groups'].append(dict(deepcopy(p91['release_groups'][0]),name='r4',start='2020-06-03T03:00:00'))

params.append(p91)


# demo  ROMS test
# Sample data subset
# https://www.seanoe.org/data/00751/86286/



def make_demo_python(demo_name):
    # write a simplified version of code to add to docs
    out=['# ' + demo_name +'.py','#---------------------------------------',
         'import oceantracker.main as main','from oceantracker.util import json_util']

    text_file = open('make_demo_plots.py', 'r')
    lines = text_file.read().splitlines()


    out += ['params = json_util.read_JSON("..\\demo_param_files\\'+ demo_name +'.json")','']
    out += ["runInfo_file_name, has_errors = main.run(params)", '']
    out +=['# output is now in output/' +demo_name,'']

    # write plot code from

    out.append('# below only required for plotting')

    plot_code = []
    started=False
    for l in lines:
        if demo_name in l:
            started=True
            continue
        if started and 'return' in l : started = False
        if started:
            if len(plot_code) ==0:
                # to remove indent by finding first non-whitespace in first line
                n1= len(l) - len(l.strip())
            plot_code.append(l[n1:]) # add without first tab

    for l in plot_code:
        if 'import' in l: out.append(l)

    out += ['','output_file= "' + path.join(path.normpath('output'), demo_name) +'"']
    for l in plot_code:
        if 'import' not in l: out.append(l)


    with open(path.join('demo_code', demo_name+'.py'), 'w') as f:
        for l in out:
            f.write(l + "\n")


def build_demos(testrun=False):
    # make json/ymal

    paramdir ='demo_param_files'
    if not path.isdir(paramdir): mkdir(paramdir)

    demo_dir = path.dirname(__file__)
    input_dir = path.join(demo_dir, 'demo_hindcast') # hindcast location

    # make all JSONS
    for demo in params:
        if demo is None or type(demo)==tuple: continue
        if type(demo) is list:
            demo_name = demo[0]['output_file_base']
            demo[0]['reader']['input_dir'] = input_dir
            demo[0]['root_output_dir'] = 'output'  # wil put in cwd
        else:
            demo_name = demo['output_file_base']
            if demo['reader'] is not None:
                demo['reader']['input_dir'] = input_dir
            demo['root_output_dir'] = 'output'  # wil put in cwd

        print('building> ', demo_name)

        json_util.write_JSON(path.join(paramdir, demo_name + '.json'), demo)
        yaml_util.write_YAML(path.join(paramdir, demo_name + '.yaml'), demo)

        make_demo_python(demo_name)
        if testrun:
            # test generated python code
            cwd= getcwd()
            chdir('demo_code')
            subprocess.call(demo_name +'.py',shell=True)
            chdir(cwd)



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-testrun', action='store_true')
    args = parser.parse_args()

    build_demos(args.testrun)
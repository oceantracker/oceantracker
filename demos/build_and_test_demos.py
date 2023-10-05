from os import path, mkdir, getcwd, chdir
import shutil
import subprocess
import argparse
import numpy as np
from oceantracker.util import json_util
from oceantracker.util import yaml_util
from copy import deepcopy
from oceantracker.main import param_template, OceanTracker

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


demo_base_params={'output_file_base' : None,
  'add_date_to_run_output_dir': False,
   'time_step' : 900,
    'debug': True,
    'reader': {"class_name": 'oceantracker.reader._base_reader._BaseReader',
                'input_dir': '.',
                'file_mask': 'demoHindcast2D*.nc',
                'search_sub_dirs': True,
                'dimension_map': {'time': 'time', 'node': 'nodes'},
                'grid_variable_map'  : {'time': 'time_sec', 'x':['east','north'],  'triangles': 'tri'},
                'field_variable_map': {'water_velocity' : ['east_vel','north_vel'],'water_depth': 'depth','tide':'tide'},
                'time_buffer_size': 15,
                'isodate_of_hindcast_time_zero': '2020-06-01'},
    'user_note':'test of notes',
    'dispersion_miss-spelt': {'A_H': .1},
    'dispersion': {'A_H': .1},
    #'pre_processing':{'my_polygons':{'class_name': 'oceantracker.pre_processing.read_geomerty.ReadCoordinates',
    #                                 'file_name':'demo_hindcast/test.geojson',
    #                                 'type':'polygon'}},
    'tracks_writer': {'turn_on_write_particle_properties_list': ['n_cell'], 'write_dry_cell_index': True},
    'release_groups': {'mypoints1':{'points': [[1594500, 5483000]], 'pulse_size': 200, 'release_interval': 0}
                                },
    'particle_properties ': {
                        'Oxygen': { 'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay', 'decay_time_scale': 1. * 3600 * 24,'initial_value' : 20.},
                        'distance_travelled':   {'class_name': 'oceantracker.particle_properties.distance_travelled.DistanceTravelled'},

                            }
    }

p1= deepcopy(demo_base_params)
p1.update({'tracks_writer':{'time_steps_per_per_file':700}}
                                )
p1.update({'output_file_base' :'demo01_plot_tracks' ,'backtracking': True,
                            'time_step': 600})
params.append(p1)

# demo 2 track animation
p2= deepcopy(demo_base_params)
p2['release_groups']={
    'point1':{'allow_release_in_dry_cells': True,'ppoint':1,
            'points': two_points, 'pulse_size': 10, 'release_interval': 3 * 3600},
    'poly1':{'class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
            'points': deepcopy(poly_points),
            'pulse_size': 10, 'release_interval': 3 * 3600}
}
p2['particle_properties'] = {'my_constant_prop': {'class_name': 'oceantracker.particle_properties.load_carrying.ParticleLoad',
                     'initial_value': 100, 'variance': 10.}}

p2.update({'block_dry_cells': True,
        'tracks_writer':{'write_dry_cell_index': True,
                                               }})
p2.update({'output_file_base' :'demo02_animation' ,'time_step': 10*60})
params.append(p2)


# demo 3
p3= deepcopy(demo_base_params)

p3['release_groups']= {
                    'myP1':  {'points': [[1596000, 5486000]], 'pulse_size': 2000, 'release_interval': 7200, 'release_radius': 100.},
                  'myP2': {'points': [[1596000, 5490000]], 'pulse_size': 2000, 'release_interval': 7200}
                    }

p3['particle_statistics'] = {'gridstats1': {'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                      'update_interval': 1800, 'particle_property_list': ['water_depth'],
                   'count_start_date': '2020-06-01 21:16:07',
                      'grid_size': [220, 221]},
            'polystats1' : {'class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased',
                      'update_interval': 1800, 'particle_property_list': ['water_depth'],
                       'polygon_list':[ {'points':poly_points}]},

            }
p3['particle_group_manager']= {'particle_buffer_chunk_size': 20000} # test buffer expansion
p3.update({ 'write_tracks': False,  'max_run_duration': 3 * 24 * 3600  })

p3.update({'output_file_base' :'demo03_heatmaps' })

params.append(p3)

# demo 4 age based heat maps
p4 = deepcopy(p3)
p4['junk']='h'
p4['particle_statistics'] = {}
p4['particle_statistics']['age_grid'] =  {'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_agedBased',
             'update_interval': 1800, 'particle_property_list': ['water_depth','water_depth_bad'],
             'grid_size': [220, 221],
             'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.}
p4['particle_statistics']['age_poly'] =          {'class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased',
             'update_interval': 1800, 'particle_property_list': ['water_depth', 'water_velocity'],
             'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.,
             'polygon_list': [{'points': poly_points} ] }

p4.update({'output_file_base' :'demo04_ageBasedHeatmaps' })

params.append (p4)

# demo 5 parallel
base_case = deepcopy(p2)

base_case.update({'output_file_base' :'demo05_parallel',
            'processors': 2,
           'advanced_settings':{ 'multiprocessing_case_start_delay' : 1.0}
          })
case_list=[]
for n in range(5):

    case_list.append({ 'release_groups': deepcopy(p2['release_groups'])})

params.append([base_case,case_list])

# track animation with settlement on reef polygon
# demo 6
p6 = deepcopy(p2)

p6['release_groups']= {
            'P1':      {'points': [[1594500, 5482700], [1598000, 5486100], [1595500, 5489700]], 'pulse_size': 10, 'release_interval': 3 * 3600},
            'poly1':  {'class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
             'points': deepcopy(poly_points),
             'pulse_size': 1, 'release_interval': 0}
            }
p6['trajectory_modifiers']= {'settle_in+polygon':
            {'class_name': 'oceantracker.trajectory_modifiers.settle_in_polygon.SettleInPolygon',
             'polygon': {'points':  deepcopy(poly_points)},
             'probability_of_settlement': .1,
             'settlement_duration': 3.*3600}}
p6.update({'output_file_base' :'demo06_reefstranding' ,'backtracking': True})
p6['particle_statistics'] = {
                    'polystats1' : {'class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased',
                    'update_interval': 1800, 'particle_property_list': ['water_depth'],
                'use_release_group_polygons': True,
                    'polygon_list':[ {'points':poly_points}]},

            }
params.append (p6)


# case 7 event logger
p7 = deepcopy(p2)

p7['release_groups']= {
        'P1':  {'points': [[1594500, 5490000], [1598000, 5488500]], 'pulse_size': 10, 'release_interval': 3 * 3600}
        }
p7['particle_properties'] ={
                'age_decay': {'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay','decay_time_scale': 1. * 3600 * 24}
                    }

p7['event_loggers']= {'in_out_poly': {'class_name': 'oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit',
                                                    'particle_prop_to_write_list' : [ 'ID','x', 'IDrelease_group', 'status', 'age'],
                                                        'polygon_list': [{'user_polygon_name' : 'A','points': (np.asarray(poly_points) + np.asarray([-5000,0])).tolist()},
                                                                         {'user_polygon_name' : 'B', 'points': poly_points_large}
                                                                         ]
                                              }
                           }


p7.update({'output_file_base' :'demo07_inside_polygon_events' })

params.append (p7)

# demo 8, particle splitting animation
p8 = deepcopy(p7)
p8['max_particles'] = 10**3

p8.update({'particle_buffer_size':  5000})

p8['release_groups']={
        'P1':{'points': [[1594500, 5483500],[1594500, 5483500+3000]], 'pulse_size': 1, 'release_interval': 0}
        }
p8['trajectory_modifiers']={'part_spliting':
           {'class_name': 'oceantracker.trajectory_modifiers.split_particles.SplitParticles',
             'splitting_interval':6*3600,
                'split_status_greater_than' : 'frozen',
                    },
        'part_culling': {'class_name': 'oceantracker.trajectory_modifiers.cull_particles.CullParticles',
             'cull_interval': 6 * 3600,
             'cull_status_greater_than': 'dead',
            'probability_of_culling': .05}
                    }

p8.update({'output_file_base' :'demo08_particle_splitting',  })
params.append (p8)

# test polygon release overlying land
p9 = deepcopy(p1)
p9.update({'output_file_base' :'demo09_polygon_release_overlapping_land',  })
p9['release_groups']={
        'Poly1': {'class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
         'points': (np.asarray(poly_points_large) + np.asarray([[0,-3000]])).tolist(),
         'pulse_size': 10, 'release_interval': 3 * 3600},
    'Poly2':{'class_name': 'oceantracker.release_groups.polygon_release_water_depth_range.PolygonReleaseWaterDepthRange',
            'min_water_depth': 30,
            'points': (np.asarray(poly_points_large) + np.asarray([[-3000, 0]])).tolist(),
            'pulse_size': 10, 'release_interval': 3 * 3600}
        }

params.append(p9)

# test polygon release overlying land
p10= deepcopy(p2)
p10.update({'output_file_base' :'demo10_polygon_residence_demo',  })

p10['release_groups']= {
        'near_shore': {'class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
            'points': (np.asarray(poly_points) + np.asarray([[-3000.,-6500]])).tolist(),
            'pulse_size': 100, 'release_interval': 12 * 3600}
        }
p10['particle_statistics']={'residentpoly': {'class_name': 'oceantracker.particle_statistics.resident_in_polygon.ResidentInPolygon',
                  'name_of_polygon_release_group':'near_shore', 'update_interval': 1800}}


params.append(p10)



# case 50 schism basic
schsim_base_params=\
{'output_file_base' :'demo50_SCHISM_depthAver', 'debug': True,'time_step': 120,
 'reader': { #'class_name': 'oceantracker.reader.schism_reader.SCHISMSreaderNCDF',
                    'input_dir': 'demo_hindcast',
                             'file_mask': 'demoHindcastSchism3D.nc',
                     'load_fields':['water_temperature']
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
                                                                     {'user_polygon_name' : 'B', 'points': poly_points_large}
                                                                     ]
                                          }}
                }

s50 = deepcopy(schsim_base_params)
s50['run_as_depth_averaged'] =  True
params.append (s50)

# schsim 3D
s56 = deepcopy(schsim_base_params)
s56['reader'].update({'depth_average': False})

s56['release_groups']={
            'P1':{'points': [[1594500, 5487000, -1], [1594500, 5483000, -1], [1598000, 5486100, -1]],
                                                     'pulse_size': 10, 'release_interval': 3600},
            'poly1': {'class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
                                    'points': poly_points, 'z_range' :[-2, -4.],
                                    'pulse_size': 10, 'release_interval':  3600}
            }
s56['velocity_modifiers']={'terminal_velocity':
       {'class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': -0.001}
                           }
s56['particle_statistics']= {'grid1':
                  {   'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                      'update_interval': 3600, 'particle_property_list': ['water_depth'], 'status_min':'moving','min_z' :-2,
                      'grid_size': [120, 121]}}


s56['resuspension'] = {'critical_friction_velocity': .005}
s56.update({'output_file_base' : 'demo56_SCHISM_3D_resupend_crtitical_friction_vel'})
s56['velocity_modifiers']= {'terminal_velocity':
                                {'class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': -0.001}
                            }
params.append (s56)

# schsim 3D, dont resupend lateral boundary test
s57 = deepcopy(s50)
s57.update({'output_file_base' : 'demo57_SCHISM_3D_lateralBoundaryTest'})
s57['dispersion'].update({'A_H':10})
s57['release_groups']={
                'P1':{'points': [[1599750, 5485600, -1]], 'pulse_size': 20, 'release_interval': 3600}
                             }

params.append(s57)

# schsim 3D, vertical section
s58 = deepcopy(s56)
s58.update({'output_file_base' : 'demo58_bottomBounce', 'backtracking': False})
s58['dispersion'].update({'A_H': 0.1, 'A_V': .005})
bc = s58

bc['velocity_modifiers']={'terminal_velocity':{'class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': -0.002,'variance': 0.0002}}
pg1= bc['release_groups']['P1']
pg1.update({'pulse_size':10,'release_interval':0, 'points': [[1593000., 5484000.+2000, -1]] }) # 1 release only
bc['release_groups']['P11']= pg1 # only point release

params.append(s58)

# schsim 3D, vertical section  with critical friction velocity
s59 = deepcopy(s58)
s59.update({'output_file_base' : 'demo59_crit_shear_resupension', 'backtracking': False})
bc = s59
bc['velocity_modifiers']['terminal_velocity']= {'class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'value': -0.002}
s59['release_groups']={ 'P1':{'points': [[1594500, 5486000, -1]],  'pulse_size':1, 'release_interval':0}}
params.append(s59)

# decaying particles sized on c
s60 = deepcopy(schsim_base_params)
s60.update({'output_file_base' : 'demo60_SCHISM_3D_decaying_particle','time_step': 120})
s60['release_groups']={
                'P1':{'points': [[1594500, 5487000, -1], [1594500, 5483000, -1], [1598000, 5486100, -1]],
                                                     'pulse_size': 1, 'release_interval': 2.5*60, 'max_age': .2*24*3600}
                        }
s60['particle_properties']= {
    'age_decay' :{'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                              'decay_time_scale':1*3600./0.14}}
s60.pop('event_loggers')
params.append(s60)

# triangle property/concetraaion plots particles sized on c
s61 = deepcopy(schsim_base_params)
s61.update({'max_run_duration': 15*24*3600.,'output_file_base': 'demo61_concentration_test'})
s61['write_tracks']= False
s61['particle_concentrations']={'outfall_conc':{'class_name':'oceantracker.particle_concentrations.particle_concentrations.ParticleConcentrations2D',
                                                          'case_output_file_tag': 'siteA','update_interval': 1800}}
s61['particle_properties']['total_water_depth']={'class_name': 'oceantracker.particle_properties.total_water_depth.TotalWaterDepth'}

for rg in s61['release_groups'].values():
    rg.update({'pulse_size': 1000, 'release_interval': 3600})

params.append(s61)
# back tracking test
p90= deepcopy(p2)

p90.update({'max_run_duration': 2*24*3600.,'output_file_base': 'demo90forward',
                                'backtracking': False,'debug': True,'time_step' :60 })
p90['reader']['time_buffer_size']=2  # test with  tiny buffer
p90['release_groups']= {
    'P1':{'pulse_size': 1, 'release_interval': 0,
           'points': [[1594500, 5486500], [1596500, 5489000], [1595000, 5483000] ]}
    }

p90['dispersion'].update({'A_H' : 0., 'A_V': 0.})

params.append(p90)

# test freewheeling when no particles
p91= deepcopy(p2) # has two points
p91.update({'output_file_base': 'demo91_free_running_gaps',
                             'time_step' :900 ,'backtracking': True})
p91['release_groups']={}
p91['release_groups']['r1'] ={'points':[two_points[1]],
                                      'max_age':6*3600,
                                      'release_interval':0,
                                      'pulse_size' : 1,
                                      'release_start_date':'2020-06-02T00:00:00' # start 1 day in 2020-06-02T21:16:07
                                      }
# 2020-06-01T05:16:07 to 2020-06-06T03:16:07
p91['release_groups']['r2'] = deepcopy(p91['release_groups']['r1'])
p91['release_groups']['r2']['release_start_date']='2020-06-03T00:00:00'

p91['release_groups']['r3'] = deepcopy(p91['release_groups']['r1']) # overlaps with last
p91['release_groups']['r3']['release_start_date']='2020-06-04T00:00:00'

p91['release_groups']['r4'] = deepcopy(p91['release_groups']['r1']) # overlaps with last
p91['release_groups']['r4']['release_start_date']='2020-06-03T03:00:00'
#p91['release_groups']['start_mid']['max_age']=2*3600
params.append(p91)


# demo 100 ROMS test
# Sample data subset
# https://www.seanoe.org/data/00751/86286/

ROMS_params={'output_file_base' :'demo70_ROMS_reader', 'debug': True,
                               'time_step': 1800,
 'reader': {'class_name': 'oceantracker.reader.ROMS_reader.ROMsNativeReader',
                    'input_dir': 'demo_hindcast',
                     'file_mask': 'DopAnV2R3-ini2007_da_his.nc',
                     'load_fields':['water_temperature']},

            'open_boundary_type': 1,
            'dispersion': {'A_H': .2, 'A_V': 0.001},
            'release_groups': {
                        'group1':{'points': [[616042, 4219971,-1],[616042, 4729971,-1],[616042, 4910000,-1]  ],
                                'pulse_size': 10, 'release_interval': 1800}
                            },
                'fields' :[{'class_name' : 'oceantracker.fields.friction_velocity.FrictionVelocity'}],
                'particle_properties':{
                 'age_decay':{'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                                                      'decay_time_scale': 1. * 3600 * 24} },
                'resupension':{'critical_friction_velocity': .00}
                }

params.append(ROMS_params)

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


    # special case of minimal example demo

    if testrun:
        from minimal_example import params as min_params

        json_util.write_JSON(path.join(paramdir, 'minimal_example.json'), min_params)
        yaml_util.write_YAML(path.join(paramdir, 'minimal_example.yaml'), min_params)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-testrun', action='store_true')
    args = parser.parse_args()

    build_demos(args.testrun)
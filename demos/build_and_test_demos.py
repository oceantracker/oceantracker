from os import path, mkdir, getcwd, chdir
import shutil
import subprocess
import argparse
import numpy as np
from oceantracker.util import json_util
from oceantracker.util import yaml_util
from copy import deepcopy

params = []
poly_points=[[1597682.1237, 5489972.7479],
                        [1598604.1667, 5490275.5488],
                        [1598886.4247, 5489464.0424],
                        [1597917.3387, 5489000],
                        [1597300, 5489000], [1597682.1237, 5489972.7479]]
poly_points_large=[[1597682.1237, 5489972.7479],
                        [1598604.1667, 5490275.5488],
                        [1598886.4247, 5489464.0424],
                        [1597917.3387, 5487000],
                        [1597300, 5487000],
                       [1597682.1237, 5489972.7479]]
demo_base_params=\
{
 'shared_params' :{'output_file_base' : None,
                   'add_date_to_run_output_dir': False,
                   },
     'reader': {"class_name": 'oceantracker.reader.generic_unstructured_reader.GenericUnstructuredReader',
                'input_dir': 'demo_hindcast',
                'file_mask': 'demoHindcast2D*.nc',
                'search_sub_dirs': True,
                'dimension_map': {'time': 'time', 'node': 'nodes'},
                'grid_variables'  : {'time': 'time_sec', 'x':['east','north'],  'triangles': 'tri'},
                'field_variables': {'water_velocity' : ['east_vel','north_vel'],'water_depth': 'depth','tide':'tide'},
                'time_buffer_size': 24,
                'isodate_of_hindcast_time_zero': '2020-06-01'},
 'base_case_params' : {
    'run_params' : {'user_note':'test of notes'},
    'dispersion': {'A_H': .1},
    'tracks_writer': {'turn_on_write_particle_properties_list': ['n_cell'], 'write_dry_cell_index': True},
    'solver': {'n_sub_steps': 2},
        'particle_release_groups': [{'points': [[1594500, 5483000]], 'pulse_size': 200, 'release_interval': 0}],
        'particle_properties': [
                        {'name': 'Oxygen', 'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay', 'decay_time_scale': 1. * 3600 * 24,'initial_value' : 20.},
                        {'class_name': 'oceantracker.particle_properties.distance_travelled.DistanceTravelled'},
                                    ],
                        }
        }

p1= deepcopy(demo_base_params)
p1.update({'case_list': [{ 'particle_release_groups': [{
           'points':  [ [1598000, 5489100]],  'pulse_size': 1, 'release_interval': 3 * 3600}]
            }]
            } )
p1['base_case_params'].update({
                               'tracks_writer':{'class_name': 'oceantracker.tracks_writer.track_writer_retangular.RectangularTrackWriter',
                                                'time_steps_per_per_file':200}})

p1['shared_params'].update({'output_file_base' :'demo01_plot_tracks' ,'backtracking': True})
params.append(p1)

# demo 2 track animation
p2= deepcopy(demo_base_params)
p2['base_case_params']['particle_release_groups']=[{'allow_release_in_dry_cells': True,
        'points': [[1594500, 5483000], [1598000, 5486100]], 'pulse_size': 10, 'release_interval': 3 * 3600},
    {'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease','name':'userA',
     'points': deepcopy(poly_points),
     'pulse_size': 10, 'release_interval': 3 * 3600}
]

p2['base_case_params'].update({'solver': {'n_sub_steps': 6}, 'run_params': {'block_dry_cells': True},
                               'tracks_writer':{'class_name': 'oceantracker.tracks_writer.track_writer_retangular.RectangularTrackWriter',
                                                'write_dry_cell_index': True,
                                               }})
p2['shared_params'].update({'output_file_base' :'demo02_animation' ,'compact_mode': True})
params.append(p2)

# demo 3
p3= deepcopy(demo_base_params)

p3['base_case_params']['particle_release_groups']=[
                  {'points': [[1596000, 5486000]], 'pulse_size': 2000, 'release_interval': 7200, 'release_radius': 100.},
                  {'points': [[1596000, 5490000]], 'pulse_size': 2000, 'release_interval': 7200}
                  ]

p3['base_case_params']['particle_statistics']=[
                  {'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                      'calculation_interval': 1800, 'particle_property_list': ['water_depth'],
                   'count_start_date': '2020-06-01 21:16:07',
                   'count_end_date': '2020-06-30 21:16:07',
                      'grid_size': [220, 221]},
                  {'class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased',
                        'count_status_in_range' : ['moving','moving'],
                      'calculation_interval': 1800, 'particle_property_list': ['water_depth'],
                       'polygon_list':[ {'points':poly_points}]}
                        ]
p3['base_case_params']['run_params'].update({ 'write_tracks': False,  'duration': 3 * 24 * 3600  })

p3['shared_params'].update({'output_file_base' :'demo03_heatmaps' })

params.append(p3)

# demo 4 age based heat maps
p4 = deepcopy(p3)
p4['base_case_params']['junk']='h'
p4['base_case_params']['particle_release_groups']=[
            {'points': [[1596000, 5486000]], 'pulse_size': 2000, 'release_interval': 7200},
            {'points': [[1596000, 5490000]], 'pulse_size': 2000, 'release_interval': 7200}
        ]
p4['base_case_params']['particle_statistics']=[
                    {'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_agedBased',
                     'calculation_interval': 1800, 'particle_property_list': ['water_depth'],
                     'grid_size': [220, 221],
                     'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.},
                    {'class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased',
                     'calculation_interval': 1800, 'particle_property_list': ['water_depth', 'water_velocity'],
                     'min_age_to_bin': 0., 'max_age_to_bin': 3. * 24 * 3600, 'age_bin_size': 3600.,
                     'polygon_list': [{'points': poly_points} ] }
                      ]
p4['shared_params'].update({'output_file_base' :'demo04_ageBasedHeatmaps' })

params.append (p4)

# demo 5 parallel
p5 = deepcopy(p2)

p5['shared_params'].update({'output_file_base' :'demo05_parallel',
                            'processors': 2, 'replicates' :1,
                            #'multiprocessing_start_method_spawn': True,
                            'multiprocessing_case_start_delay' : 1.0})

pg= deepcopy(p5['base_case_params']['particle_release_groups'][0])
p5['base_case_params']['particle_release_groups'] =[]

pg.update({'pulse_size': 2})
c= {'run_params' : {},
    'particle_release_groups' : [pg]}
p5['case_list'] = []
for n in range(5):
    p= deepcopy(c)
    p['run_params']['case_output_file_tag']='test_case_tag_' + str(n)
    p5['case_list'].append(p)

params.append (p5)

# track animation with settlement on reef polygon
# demo 6
p6 = deepcopy(p2)
p6['base_case_params'].update({'solver': {'n_sub_steps': 6}})

p6['base_case_params']['particle_release_groups']= [
            {'points': [[1594500, 5482700], [1598000, 5486100], [1595500, 5489700]], 'pulse_size': 10, 'release_interval': 3 * 3600},
            {'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease',
             'points': deepcopy(poly_points),
             'pulse_size': 1, 'release_interval': 0}   ]
p6['base_case_params']['trajectory_modifiers']=  [
            {'class_name': 'oceantracker.trajectory_modifiers.settle_in_polygon.SettleInPolygon',
             'polygon': {'points':  deepcopy(poly_points)},
             'probability_of_settlement': .1,
             'settlement_duration': 3.*3600}]
p6['shared_params'].update({'output_file_base' :'demo06_reefstranding' ,'backtracking': True})
params.append (p6)


# case 7 event logger
p7 = deepcopy(p2)

p7['base_case_params']['particle_release_groups']= [
            {'points': [[1594500, 5490000], [1598000, 5488500]], 'pulse_size': 10, 'release_interval': 3 * 3600}            ]
p7['base_case_params']['particle_properties'] =[{'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay','decay_time_scale': 1. * 3600 * 24}]

p7['base_case_params']['event_loggers'] =[{'class_name': 'oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit',
                                                    'particle_prop_to_write_list' : [ 'ID','x', 'IDrelease_group', 'status', 'age'],
                                                        'polygon_list': [{'user_polygon_name' : 'A','points': (np.asarray(poly_points) + np.asarray([-5000,0])).tolist()},
                                                                         {'user_polygon_name' : 'B', 'points': poly_points_large}
                                                                         ]
                                              }]


p7['shared_params'].update({'output_file_base' :'demo07_inside_polygon_events' })

params.append (p7)

# demo 8, particle splitting animation
p8 = deepcopy(p7)
p8['shared_params'][ 'compact_mode'] =False
p8['base_case_params']['run_params'].update({'retain_culled_part_locations' : True,'particle_buffer_size':  5000})

p8['base_case_params']['particle_release_groups']=[{'points': [[1594500, 5483500],[1594500, 5483500+3000]], 'pulse_size': 1, 'release_interval': 0}  ]
p8['base_case_params']['trajectory_modifiers']=[
           {'class_name': 'oceantracker.trajectory_modifiers.split_particles.SplitParticles',
             'splitting_interval':6*3600,
                'split_status_greater_than' : 'frozen',
                    },
           {'class_name': 'oceantracker.trajectory_modifiers.cull_particles.CullParticles',
             'cull_interval': 6 * 3600,
             'cull_status_greater_than': 'dead',
            'probability_of_culling': .05}
             ]

p8['shared_params'].update({'output_file_base' :'demo08_particle_splitting',  })
params.append (p8)

# test polygon release overlying land
p9 = deepcopy(p1)
p9['shared_params'].update({'output_file_base' :'demo09_polygon_release_overlapping_land',  })
p9['base_case_params']['particle_release_groups']=[
        {'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease',
         'points': (np.asarray(poly_points_large) + np.asarray([[0,-3000]])).tolist(),
         'pulse_size': 10, 'release_interval': 3 * 3600},
    {'class_name': 'oceantracker.particle_release_groups.polygon_release_water_depth_range.PolygonReleaseWaterDepthRange',
    'min_water_depth': 30,
     'points': (np.asarray(poly_points_large) + np.asarray([[-3000, 0]])).tolist(),
     'pulse_size': 10, 'release_interval': 3 * 3600}
        ]

params.append(p9)

# test polygon release overlying land
p10= deepcopy(p2)
p10['shared_params'].update({'output_file_base' :'demo10_polygon_residence_demo',  })

p10['base_case_params']['particle_release_groups']=[
        {'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease',
         'points': (np.asarray(poly_points) + np.asarray([[-3000.,-6500]])).tolist(),'name': 'near_shore',
         'pulse_size': 100, 'release_interval': 12 * 3600}
        ]
p10['base_case_params']['particle_statistics']=[
                  {'class_name': 'oceantracker.particle_statistics.resident_in_polygon.ResidentInPolygon',
                  'name_of_polygon_release_group':'near_shore', 'calculation_interval': 1800}]

params.append(p10)



# case 50 schism basic
schsim_base_params=\
{'shared_params' :{'output_file_base' :'demo50_SCHISM_depthAver', 'debug': True},
 'reader': {'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',
                    'input_dir': 'demo_hindcast',
                             'file_mask': 'demoHindcastSchism3D.nc',
                            'depth_average': True,
                     'field_variables':{'water_temperature':'temp'}
                          },
 'base_case_params' : { 'run_params' : {},
                 'dispersion': {'A_H': .2, 'A_V': 0.001},
                        'solver': {'n_sub_steps': 30},
                'particle_release_groups': [{'points': [[1595000, 5482600, -1],[1599000, 5486200, -1] ],
                                                     'pulse_size': 10, 'release_interval': 3600,
                                                    'allow_release_in_dry_cells': True},
                                                    {'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease',
                                    'points': poly_points,
                                    'pulse_size': 10, 'release_interval':  3600}
                                                    ],
                'particle_properties': [{'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                                                      'decay_time_scale': 1. * 3600 * 24} ],
                'event_loggers':[{'class_name': 'oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit',
                                                    'particle_prop_to_write_list' : [ 'ID','x', 'IDrelease_group', 'status', 'age'],
                                                        'polygon_list': [{'user_polygon_name' : 'A','points': (np.asarray(poly_points) + np.asarray([-5000,0])).tolist()},
                                                                         {'user_polygon_name' : 'B', 'points': poly_points_large}
                                                                         ]
                                              }]
                }
}

s50 = deepcopy(schsim_base_params)
params.append (s50)

# schsim 3D
s55 = deepcopy(schsim_base_params)
s55['shared_params'].update({'output_file_base' : 'demo55_SCHISM_3D_fall_velocity'})
s55['reader'].update({'depth_average': False,'field_variables_to_depth_average' :[ 'water_velocity', 'salt', 'water_temperature']})

s55['base_case_params']['particle_release_groups']=[{'points': [[1594500, 5487000, -1], [1594500, 5483000, -1], [1598000, 5486100, -1]],
                                                     'pulse_size': 10, 'release_interval': 3600},
                                                    {'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease',
                                    'points': poly_points, 'z_range' :[-2, -4.],
                                    'pulse_size': 10, 'release_interval':  3600}
                                                    ]
s55['base_case_params']['velocity_modifiers']= [
       {'class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'mean': -0.001}
]
s55['base_case_params']['fields']=[{'class_name' : 'oceantracker.fields.friction_velocity.FrictionVelocity'}]
s55['base_case_params']['solver'] = {'n_sub_steps': 30}
s55['base_case_params']['particle_statistics']=[
                  {   'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                      'calculation_interval': 3600, 'particle_property_list': ['water_depth'],
                      'grid_size': [120, 121]}]
#s55['base_case_params']['dispersion'] = {'A_V': 0,'A_H': 0} # testing
params.append(s55)

# schsim 3D, sometimes resupend
s56 = deepcopy(s55)
s56['base_case_params']['trajectory_modifiers'] = [{'class_name': 'oceantracker.trajectory_modifiers.resuspension.BasicResuspension',
                                                    'critical_friction_velocity': .005}]
s56['shared_params'].update({'output_file_base' : 'demo56_SCHISM_3D_resupend_crtitical_friction_vel', 'compact_mode': True})
s56['base_case_params']['velocity_modifiers']= [
       {'class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'mean': -0.001}]
#s56['base_case_params']['particle_release_groups']=[{'points': [[1594500, 5487000, -1], [1594500, 5483000, -1], [1598000, 5486100, -1]], 'pulse_size': 20, 'release_interval': 0}]
params.append (s56)

# schsim 3D, dont resupend lateral boundary test
s57 = deepcopy(s50)
s57['shared_params'].update({'output_file_base' : 'demo57_SCHISM_3D_lateralBoundaryTest'})
s57['base_case_params']['dispersion'].update({'A_H':10})
s57['base_case_params']['particle_release_groups']=[{'points': [[1599750, 5485600, -1]], 'pulse_size': 20, 'release_interval': 3600}]

params.append(s57)

# schsim 3D, vertical section
s58 = deepcopy(s56)
s58['shared_params'].update({'output_file_base' : 'demo58_bottomBounce', 'backtracking': False})
s58['base_case_params']['dispersion'].update({'A_H': 0.1, 'A_V': .005})
bc = s58['base_case_params']

bc['trajectory_modifiers'] =[{'class_name': 'oceantracker.trajectory_modifiers.resuspension.BasicResuspension','critical_friction_velocity': .01}]
bc['velocity_modifiers']= [{'class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'mean': -0.002,'variance': 0.0002}]
pg1= bc['particle_release_groups'][0]
pg1.update({'pulse_size':10,'release_interval':0, 'points': [[1593000., 5484000.+2000, -1]] }) # 1 release only
bc['particle_release_groups'] = [pg1] # only point release


params.append(s58)

# schsim 3D, vertical section  with critical friction velocity
s59 = deepcopy(s58)
s59['shared_params'].update({'output_file_base' : 'demo59_crit_shear_resupension', 'backtracking': False})
bc = s59['base_case_params']
bc['trajectory_modifiers'] =[{'class_name': 'oceantracker.trajectory_modifiers.resuspension.BasicResuspension',
                                   'critical_friction_velocity': .01}]
bc['velocity_modifiers']= [{'class_name' : 'oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity', 'mean': -0.0005}]
params.append(s59)

# decaying particles sized on c
s60 = deepcopy(schsim_base_params)
s60['shared_params'].update({'output_file_base' : 'demo60_SCHISM_3D_decaying_particle','compact_mode':True})
s60['base_case_params']['solver'] = {'n_sub_steps': 48}
s60['base_case_params']['particle_release_groups']=[{'points': [[1594500, 5487000, -1], [1594500, 5483000, -1], [1598000, 5486100, -1]],
                                                     'pulse_size': 1, 'release_interval': 2.5*60, 'maximum_age': .2*24*3600}
                                                    ]
s60['base_case_params']['particle_properties']= [{'name': 'C', 'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                              'decay_time_scale':1*3600./0.14}]
s60['base_case_params'].pop('event_loggers')
params.append(s60)

# triangle property/concetraaion plots particles sized on c
s61 = deepcopy(schsim_base_params)
s61['shared_params'].update({'max_duration': 15*24*3600.,'output_file_base': 'demo61_concentration_test'})
s61['base_case_params']['run_params']['write_tracks']= False
s61['base_case_params']['particle_concentrations']=[{'class_name':'oceantracker.particle_concentrations.particle_concentrations.ParticleConcentrations2D',
                                                          'case_output_file_tag': 'siteA','calculation_interval': 1800}]
s61['base_case_params']['particle_properties'].append({'class_name': 'oceantracker.particle_properties.total_water_depth.TotalWaterDepth'})

for rg in s61['base_case_params']['particle_release_groups']:
    rg.update({'pulse_size': 1000, 'release_interval': 3600})

params.append(s61)
# back tracking test
p90= deepcopy(p2)

p90['shared_params'].update({'max_duration': 1*24*3600.,'output_file_base': 'demo90forward',
                                'backtracking': False,'debug': True })

p90['base_case_params']['particle_release_groups']= [{'pulse_size': 1, 'release_interval': 0,
                                                        'points': [[1594500, 5486500], [1596500, 5489000], [1595000, 5483000] ]}]
p90['base_case_params']['solver']['n_sub_steps'] =  60
p90['base_case_params']['dispersion'].update({'A_H' : 0., 'A_V': 0.})

params.append(p90)


# demo 100 ROMS test
# Sample data subset
# https://www.seanoe.org/data/00751/86286/

ROMS_params={'shared_params' :{'output_file_base' :'demo70_ROMS_reader', 'debug': True},
 'reader': {'class_name': 'oceantracker.reader.dev_ROMS_reader.ROMS',
                    'input_dir': 'demo_hindcast',
                     'file_mask': 'DopAnV2R3-ini2007_da_his.nc',
                     'field_variables':{'water_temperature':'temp'}
                          },
 'base_case_params' : { 'run_params' : {'open_boundary_type': 1}, 'dispersion': {'A_H': .2, 'A_V': 0.001},
                        'solver': {'n_sub_steps': 6},
                'particle_release_groups': [{'points': [[616042, 4219971,-1],[616042, 4729971,-1],[616042, 4910000,-1]  ],
                                                     'pulse_size': 10, 'release_interval': 1800,
                                                 }
                                                    ],
                'fields' :[{'class_name' : 'oceantracker.fields.friction_velocity.FrictionVelocity'}],
                'particle_properties': [{'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                                                      'decay_time_scale': 1. * 3600 * 24} ],
                'trajectory_modifiers':[{'class_name': 'oceantracker.trajectory_modifiers.resuspension.BasicResuspension',
                                   'critical_friction_velocity': .00}]
                }
}

params.append(ROMS_params)

def make_demo_python(demo_name):
    # write a simplified version of code to add to docs
    out=['# ' + demo_name +'.py','#---------------------------------------',
         'import oceantracker.main as main','from oceantracker.util import json_util']

    text_file = open('make_demo_plots.py', 'r')
    lines = text_file.read().splitlines()


    out += ['params = json_util.read_JSON("..\\demo_json\\'+ demo_name +'.json")','']
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

    JSONdir ='demo_json'
    if not path.isdir(JSONdir): mkdir(JSONdir)
    YAMLdir = 'demo_yaml'
    if not path.isdir(YAMLdir): mkdir(YAMLdir)
    demo_dir = path.dirname(__file__)
    input_dir = path.join(demo_dir, 'demo_hindcast') # hindcast location

    # make all JSONS
    for demo in params:
        if demo is None: continue
        demo_name = demo['shared_params']['output_file_base']
        print('building> ', demo_name)
        demo['reader']['input_dir'] = input_dir
        demo['shared_params']['root_output_dir'] = 'output' # wil put in cwd

        json_file=path.join(JSONdir, demo_name + '.json')
        json_util.write_JSON(json_file, demo)

        yaml_file= path.join(YAMLdir, demo_name + '.yaml')
        yaml_util.write_YAML(yaml_file, demo)

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

        json_util.write_JSON(path.join(JSONdir, 'minimal_example.json'), min_params)
        yaml_util.write_YAML(path.join(YAMLdir, 'minimal_example.yaml'), min_params)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-testrun', action='store_true')
    args = parser.parse_args()

    build_demos(args.testrun)
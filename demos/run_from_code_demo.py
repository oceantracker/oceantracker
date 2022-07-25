# run oceantracker direct from code from dictionary built in code
# make polygons staggered to south west, by appending polygon release groups
import numpy as np
from oceantracker.main import run
from oceantracker.post_processing.read_output_files import load_output_files
from oceantracker.post_processing.plotting.plot_tracks import plot_tracks

params={
'shared_params' :{
                  'output_file_base' :'demo1000_runFromCodeDemo',
                  'root_output_dir': 'output', 'debug': True,
                  'backtracking': False},
 'reader':  { "class_name": 'oceantracker.reader.generic_unstructured_reader.GenericUnstructuredReader',
              'input_dir': 'demo_hindcast',
              'file_mask': 'demoHindcast2D*.nc',
              'search_sub_dirs': True,
              'dimension_map': {'time': 'time', 'z': None,'node': 'nodes'},
                'grid_variables': {'time': 'time_sec',
                                    'x': [ 'east', 'north'],
                                   'triangles': 'tri'},
                'field_variables' :{'water_depth' : 'depth', 'water_velocity': ['east_vel','north_vel']},
                'time_buffer_size': 24, 'isodate_of_hindcast_time_zero': '2000-01-01'} ,
 'base_case_params' : {
    'run_params' : {},
    'dispersion': {'A_H': 1.},
    'solver': {'n_sub_steps': 12},
        'particle_release_groups': [],
                                  }
 }

poly_points=np.asarray([[1597682.1237, 5489972.7479],
                        [1598604.1667, 5490275.5488],
                        [1598886.4247, 5489464.0424],
                        [1597917.3387, 5489000],
                        [1597300, 5489000], [1597682.1237, 5489972.7479]])

# make polygons staggered to south west, by appending polygon release groups
for n in range(4):
    points=poly_points+np.asarray([[-1050*n,-2100*n]])
    params['base_case_params']['particle_release_groups'].append({'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease',
                                                                 'points': points.tolist(), 'pulse_size': 10, 'release_interval': 2*3600})

runInfo_file_name, has_errors = run(params)
caseInfoFile = load_output_files.get_case_info_file_from_run_file(runInfo_file_name)
plot_tracks.animate_particles(caseInfoFile, axis_lims=[1590800, 1601800, 5478700, 5491200],
                                title='Run from code demo, staggered polygons', back_ground_depth=True)
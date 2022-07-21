from os import path
import argparse
import glob
from oceantracker.util import basic_util
from oceantracker.main import run
import  oceantracker.post_processing.plotting.plot_heat_maps as otPlot


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-noplot', action='store_true')
    parser.add_argument('-build', action='store_true')
    parser.add_argument('-threeD', action='store_true')

    parser.add_argument('--demo', default=None, type= int)
    parser.add_argument('-mode_debug', action='store_true')
    args = parser.parse_args()

    params= { 'shared_params' : {
                                 'root_output_dir': '..\\tests\\output',
                                 'output_file_base' : 'testStucturedGridReaderV01',
                                 'debug' : True,
                                 'max_duration' : 1*24*3600.
                                },

            'reader': {"class_name": "oceantracker.reader.dev_genericStucturedGridReader.GenericStucturedGridReader",'input_dir' : 'F:\\\Hindcasts\\\BOP_POM_Hindcast\\',
                       #"class_name": "oceantracker.reader.generic_ncdf_readerUnstructured.GenericReaderNCDF",
                    'file_mask': 'circFlow2DT*.nc',
                    'field_variables':{  'water_velocity': [{'file_var' :'u','components': [0]},{'file_var' :'v','components': [1]}],
                                         'water_depth' :'depth'
                                        },
                    'grid_variables':{      'time':'time',
                                            'triangles' : None,
                                            'dry_cells' : None,
                                            'x':[{'file_var' :'lat','components': [0]},{'file_var' :'lon','components': [1]}],
                                        },
                  'dimension_map': {'node': None, 'time': 'time','z':None,  'x':'lon',  'y':'lat'},
                   'time_buffer_size': 500,
                   'isodate_of_hindcast_time_zero': '2011-02-01'},

              'base_case_params':{'particle_release_groups' : [{'points' : [[5000., 0.]], 'pulse_size': 1000}]

              }
             }

    run_info_file= run(params)
    otPlot.animate_particles(run_info_file,  title='3 hourly point and polygon releases with tidal stranding')

    if args.threeD:
        params['input_dir'] = '../tests/testData'
        params['output_file_base'] = 'test3D'

        p= params['case_list'][0]['particle_release_groups'][0]['points']
        p[0].append(0.)
        p[1].append(0.)
        ot = OceanTrackerRunner()
        ot.solve_for_data_in_buffer(params)
        log = json_util.read_JSON(path.join(params['root_output_dir'], params['output_file_base'] + '_log.json'))
        otPlot.animate_particles(log['info']['tracks_writer']['file_name'], axes=[1590800, 1601800, 5478700, 5491200],
                             text='3 hourly point and polygon releases with tidal stranding')




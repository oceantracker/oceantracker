from os import path
import argparse

from oceantracker.util import basic_util
from next_oceanTrackerSim import OceanTrackerRunner
import  oceantracker.post_processing.plotting.plot_statistics as otPlot


def get_params(args):
    shared_params={'debug': True,


         'root_output_dir': 'output\\nextOTsim',
        'reader': {'file_mask': 'demoHindcast2D*.nc','input_dir': '../demos/demo_hindcast',
                   'water_velocity_map': {'u': 'east_vel', 'v': 'north_vel'},
                   'field_map': {},
                   'dimension_map': {'space': 'node', 'time': 'time'},
                   'grid_map': {'time': 'time_sec',
                                'x': 'east', 'y': 'north',
                                'triangles': 'tri',
                                },
                   'time_buffer_size': 48,
                   'isodate_of_hindcast_time_zero': '2017-01-01'}
                  }
    base_case_params = {'output_file_base':'nextOTsim','particle_release_groups': [
            {'points': [[1594500, 5482700]], 'pulse_size': 5, 'release_interval': 3600}, ],
        'logFileWriter' : 'next_writeLogFile',
                        'solver': {'n_sub_steps': 6},
                          }

    case_params= {

        'dispersion': {'A_H': 0.1},

        'particle_properties': [{'class_name': 'oceantracker.particle_properties.age_decay.age_decay',
                                      'decay_time_scale': 1. * 3600 * 24},
                                     ],
  }

    params = {'shared_params':shared_params, 'base_case_params': base_case_params , 'case_list': [case_params] }

    return params


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-noplot', action='store_true')
    parser.add_argument('-build', action='store_true')
    parser.add_argument('-threeD', action='store_true')

    parser.add_argument('--demo', default=None, type= int)
    parser.add_argument('-debug', action='store_true')
    args = parser.parse_args()


    params= get_params(args)

    ot = OceanTrackerRunner()


    ot.solve_for_data_in_buffer(params)
    fn =path.join(params['shared_params']['root_output_dir'], params['base_case_params']['output_file_base'] + '_log.json')
    log = json_util.read_JSON(fn)
    otPlot.animate_particles(log['info']['tracks_writer']['file_name'], axes=[1590800, 1601800, 5478700, 5491200],
                             text='3 hourly point and polygon releases with tidal stranding')


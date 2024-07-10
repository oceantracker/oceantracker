from os import path
from oceantracker.main import OceanTracker
from plot_oceantracker import plot_statistics

import numpy as np
from tests.unit_tests import test_definitions
from plot_oceantracker.plot_tracks import animate_particles
from read_oceantracker.python import load_output_files
# double gyre https://shaddenlab.berkeley.edu/uploads/LCS-tutorial/examples.html

def _run(args):
    # defaults
    model_settings=dict(
                grid_size = [100, 200],
                write_intermediate_results = True,
                grid_span = None,
                grid_center = None,
                release_interval = 0,
                lags = None,
                #floating = True,
                )
    settings= dict(time_step=900, backtracking= args.backtracking)

    match args.variant:
        case 0:
            label='demoSchism'
            hm = test_definitions.hydro_model['demoSchism']
            model_settings.update(
                grid_size=[90, 120],
                grid_span=[6000, 8000],
                grid_center=[1594000, 5484200],
                release_interval=1800,
                lags=[3 * 3600])

        case 1:
            # double gyre https://shaddenlab.berkeley.edu/uploads/LCS-tutorial/examples.html
            label = 'doubleGyre'
            hm = test_definitions.hydro_model['doubleGyre']
            model_settings.update(
                grid_size=[200, 400],
                grid_span=[2 - 1 / 100, 1 - 1 / 100],
                grid_center=[1, .5],
                lags=[15])
            settings.update(time_step=.25/4)

        case 2:
            label='NZnational_auck'
            hm = test_definitions.hydro_model['NZnational']
            model_settings.update(
                grid_size=[100, 100],
                grid_span=[60000, 60000],
                grid_center=hm['x0'][2],
                release_interval=3600,
                lags=[12.42* 3600])
            settings.update(max_run_duration=7*24*3600, time_step=3600)
        case 3:
            label='sounds'
            hm = test_definitions.hydro_model['sounds']
            model_settings.update(
                grid_size=[100, 100],
                grid_span=[10000, 10000],
                grid_center=hm['x0'][1],
                release_interval=3600,
                lags=[2*24* 3600])
            settings.update(max_run_duration=7*24*3600, time_step=3600)
    #setup run
    ot = OceanTracker()

    ot.add_class('reader', **hm['reader'])
    ot.settings(**test_definitions.base_settings(__file__, args, label))
    ot.settings(**settings)

    ot.add_class('integrated_model',
                 class_name= 'dev_LagarangianStructuresFTLE2D',
                **model_settings)
    case_info_file_name= ot.run()

    LCS_data = load_output_files.load_LSC(case_info_file_name)

    match args.variant:
        case 0:
            plot_statistics.plot_LCS(LCS_data, n_time_step=None)
        case 1:
            plot_statistics.plot_LCS(LCS_data, n_time_step=-1)
        case 2:
            plot_statistics.plot_LCS(LCS_data)
        case 3:
            plot_statistics.plot_LCS(LCS_data)
    return None


def main(args):
    if args.variant is None:
        for v in [0,1,2]:
            args.variant=v
            _run(args)
    else:
        _run(args)


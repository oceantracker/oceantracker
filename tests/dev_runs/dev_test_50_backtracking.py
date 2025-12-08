from os import path
from oceantracker.main import OceanTracker
import   dd
import numpy as np
from oceantracker.read_output.python import load_output_files

from copy import deepcopy

def main(args):


    ci =[]
    for n, p in enumerate(['forwards', 'backwards']):
        ot = OceanTracker()
        ot.settings(**dd.base_settings(__file__,args))

        ot.settings(max_run_duration=  2 * 24 * 3600., use_dispersion=False,
                    backtracking=False if n == 0 else True,
                    time_step= 60,
                    output_file_base= ot.params['output_file_base'] + '_run_' + p,
                    time_buffer_size=2) # test with  tiny buffer
        hm = dd.hydro_model['demoSchism2D']
        ot.add_class('reader', **hm['reader'])
        ot.add_class('tracks_writer', update_interval=60, write_dry_cell_flag=False)

        if n == 0:
            points = [[1594500, 5486500], [1596500, 5489000], [1595000, 5483000]]
            start = None
        else:
            # run backwards from end of forwards
            tracks = dd.load_tracks(ci[0])
            points = tracks['x'][-1]
            start = tracks['time'][-1]

        ot.add_class('release_groups', name='P1', pulse_size=1,
                     start=start,
                     release_interval=0, points=points,
                     )

        ci.append(ot.run())

    if args.plot:
        from matplotlib import pyplot as plt
        from oceantracker.plot_output import plot_utilities

        tf = load_output_files.load_track_data(ci[0])
        bf = load_output_files.load_track_data(ci[1])


        ax_lims = [1591000, 1601500, 5478500, 5491000]
        # have run forwards now backwards from last location
        plt.clf()
        ax = plt.gca()
        plot_utilities.draw_base_map(tf['grid'], ax=ax, show_grid=True, axis_lims=ax_lims,
                                     # title='Back tracking, forward=Green, back=Red', text1='start=Green dot, 1 day- 1 min time steps'
                                     )

        ax.plot(tf['x'][:, :, 0], tf['x'][:, :, 1], color='g', linewidth=3)
        ax.scatter(tf['x'][0, :, 0], tf['x'][0, :, 1], color='g', marker='o', s=20, zorder=9)

        ax.plot(bf['x'][:, :, 0], bf['x'][:, :, 1], color='y', linewidth=1, )
        ax.scatter(bf['x'][0, :, 0], bf['x'][0, :, 1], color='y', marker='o', s=20, zorder=9)

        plt.show()

        # rerun backwards from end point of forwards run
        #start_date = str(time_util.seconds_to_datetime64(d90['time'][-1]))
        if False:
            params['output_file_base'] = 'Demo90backward'
            params['backtracking'] = True
            params['use_dispersion'] = False
            params['release_groups'][0].update({'points': d90['x'][-1, :, :], 'start': start_date})

            print('backtracking start', start_date)

            caseInfoFile2 = main.run(params)
            d2 = load_output_files.load_track_data(caseInfoFile2)

            ax.plot(d2['x'][:, :, 0], d2['x'][:, :, 1], color='y', linewidth=1, linestyle='dashed')
            ax.scatter(d2['x'][0, :, 0], d2['x'][0, :, 1], color='y', marker='o', s=20, zorder=9)
            ax.set_title('Test particle tracking forwards then backwards')
            plt.gcf().tight_layout()
            plot_utilities.show_output(plot_file_name='output\\' + demo_name + '_and_backward_tracks.jpeg')




from os import path, mkdir, getcwd
import argparse
import glob
import matplotlib.pyplot as plt
from oceantracker.util import json_util
from oceantracker.util import time_util

from oceantracker import main
from plot_oceantracker import plot_utilities
import make_demo_plots
import build_and_test_demos
import numpy as np
from read_oceantracker.python import load_output_files
from read_oceantracker.python.load_output_files import load_stats_data, load_concentration_data
from plot_oceantracker.plot_statistics import plot_heat_map, animate_heat_map

two_points= [[1594500, 5483000], [1598000, 5486100]]

    
if __name__ == "__main__":
    # run demos from build json files

    parser = argparse.ArgumentParser()
    parser.add_argument('-noplot', action='store_true')
    parser.add_argument('-skiprun', action='store_true')
    parser.add_argument('--demo', default=None, type= int)
    parser.add_argument('--root_output_dir', default='output', type=str)
    parser.add_argument('-save_plot', action='store_true')
    parser.add_argument('-testing', action='store_true')
    args = parser.parse_args()

    np.random.seed(0)

    build_and_test_demos.build_demos()


    if args.root_output_dir is None:  args.root_output_dir = getcwd()

    if not path.isdir(args.root_output_dir):  mkdir(args.root_output_dir)

    demo_dir = path.dirname(__file__)
    param_dir = path.join(demo_dir, 'demo_param_files')

    if args.demo is None:
        # build full list of   demos
        demo_list=[]
        demofiles = glob.glob(path.join(param_dir, 'demo*.json'))
        for f in demofiles:
            demo_list.append(int(path.split(f)[1][4:6]))
        demo_list.sort()
    else:
        demo_list=[args.demo]

    test_demo=1000
    if  args.testing:
        demo_list=[test_demo] # ros ver
    else:
        # get rid of d deveopment demos
        demo_list2=[]
        for d in demo_list:
            if d != test_demo : demo_list2.append((d))
        demo_list= demo_list2

    for n in demo_list:

        f=glob.glob(path.join(param_dir, 'demo' + '%02.0f' % n + '*.json'))
        if len(f)==0:
            exit('runOTdemos.py: No demo file number ' + str(n))

        params = json_util.read_JSON(f[0])

        if type(params) is list:
            demo_name = params[0]['output_file_base']
            if params[0]['reader'] is not None:
                params[0]['reader']['input_dir'] = path.join(path.dirname(__file__), 'demo_hindcast')
            output_folder = path.join(params[0]['root_output_dir'], params[0]['output_file_base'])
            params[0]['root_output_dir'] = 'output'
        else:
            params['USE_random_seed'] = True
            demo_name = params['output_file_base']
            if params['reader'] is not None:
                params['reader']['input_dir'] = path.join(path.dirname(__file__), 'demo_hindcast')
            params['root_output_dir'] = 'output'
            output_folder = path.join(params['root_output_dir'], params['output_file_base'])

        if n==0:
            # demo zero tests help class
            from oceantracker.main import OceanTracker
            ot = OceanTracker()

            ot.settings(output_file_base='demo00_helper_class_test',
                        time_step=600)
            ot.add_class('reader', input_dir='demo_hindcast',
                         file_mask='demoHindcastSchism3D.nc')
            ot.add_class('release_groups', name='my_point1', points=two_points,case=0)
            ot.add_class('release_groups', name='my_point1', points=two_points,case=1)

            ot.add_class('dispersion', A_H=1)
            ot.run()

            continue


        elif not args.skiprun:
            if type(params) == list:
                case_info_file_name = main.run_parallel(params[0], params[1])
            else:
                case_info_file_name = main.run(params)

            if case_info_file_name is None:
                print('Error during demo')
                exit()
            if type(params) is list:  continue

        # no plotting // cases
        else:
            case_info_file_name =path.join('output', params['output_file_base'],params['output_file_base']+'_caseInfo.json')

        anim= None
        fps=15

        if args.noplot:
            output_file_base= None
        else:
            output_file_base = path.join('output', params['output_file_base'])

        if  args.noplot : continue

        if args.testing:
            #tracks=load_output_files.load_track_data(case_info_file_name)
            #from plot_oceantracker.plot_utilities import display_grid
            #display_grid(tracks['grid'],ginput=3)
            pass

        plot_output_file = output_file_base if args.save_plot else None



        # do plots
        if n==3:
            # time heat maps
            poly_stats_data = load_stats_data(case_info_file_name, name='polystats1')

            stats_data = load_stats_data(case_info_file_name, name='gridstats1')
            axis_lims = [1591000, 1601500, 5478500, 5491000]
            animate_heat_map(stats_data, 'myP1', axis_lims=axis_lims,
                             heading='Particle count heatmaps built on the fly, no tracks recorded, log scale',
                             movie_file=plot_output_file + '.mp4' if plot_output_file is not None else None,
                             fps=7)
            plot_heat_map(stats_data, 'myP1', axis_lims=axis_lims, var='water_depth', heading='Water depth built on the fly, no tracks recorded',
                          plot_file_name=plot_output_file + '_water_depth.jpeg' if plot_output_file is not None else None)

        elif n == 61:
            #todo make conc plotting work

            from plot_oceantracker.plot_statistics import animate_concentrations

            c = load_concentration_data(case_info_file_name)

            axis_lims = [1591000, 1601500, 5478500, 5491000]

            animate_concentrations(c, plot_load=False, logscale=True,
                                   axis_lims=axis_lims, cmap='hot_r',
                                   heading='SCHISIM-3D, 2D concentrations in triangles, shading',
                                   movie_file=plot_output_file + '_shading.mp4' if plot_output_file is not None else None,
                                   fps=7, interval=20,
                                   vmin=0., vmax=1.0)
            animate_concentrations(c, plot_load=True, logscale=True,
                                   axis_lims=axis_lims, cmap='hot_r', shading=False, interval=200,
                                   heading='SCHISIM-3D, 2D particle counts in triangles, noshading',
                                   fps=7,
                                   movie_file=plot_output_file + '_noshading.mp4' if plot_output_file is not None else None,
                                   )

        elif 0 < n < 90:

            getattr(make_demo_plots,demo_name)(case_info_file_name, plot_output_file)

        elif n> 0 :
            if n==90:
                ax_lims = [1591000, 1601500, 5478500, 5491000]
                # have run forwards now backwards from last location
                plt.clf()
                ax= plt.gca()
                d90 = load_output_files.load_track_data(case_info_file_name)
                plot_utilities.draw_base_map(d90['grid'], ax=ax, show_grid=True, axis_lims=ax_lims,
                                             #title='Back tracking, forward=Green, back=Red', text1='start=Green dot, 1 day- 1 min time steps'
                                             )

                ax.plot(d90['x'][:, :, 0], d90['x'][:, :, 1], color='g', linewidth=3)
                ax.scatter(d90['x'][0, :, 0], d90['x'][0, :, 1], color='g', marker='o', s=20, zorder=9)

                # rerun backwards from end point of forwards run
                start_date = str(time_util.seconds_to_datetime64(d90['time'][-1]))

                params['output_file_base'] = 'Demo90backward'
                params['backtracking'] = True
                params['include_dispersion']= False
                params['release_groups']['P1'].update({ 'points': d90['x'][-1, :, :], 'start': start_date})

                print('backtracking start', start_date)

                caseInfoFile2 = main.run(params)
                d2 = load_output_files.load_track_data(caseInfoFile2)

                ax.plot(d2['x'][:, :, 0], d2['x'][:, :, 1], color='y', linewidth=1,linestyle='dashed')
                ax.scatter(d2['x'][0, :, 0], d2['x'][0, :, 1], color='y', marker='o', s=20, zorder=9)
                ax.set_title('Test particle tracking forwards then backwards')
                plt.gcf().tight_layout()
                plot_utilities.show_output(plot_file_name='output\\' + demo_name + '_and_backward_tracks.jpeg')
            elif n==91:

                track_data = load_output_files.load_track_data(case_info_file_name)
                t = track_data['time'].astype('datetime64[s]')
                plt.plot(t)
                plt.title('Free running between release groups')
                plt.ylabel('Date')
                plt.ylabel('Recorded time step')
                plt.show()


                plt.scatter(t,np.sum(track_data['status'] >= track_data['particle_status_flags']['stationary'], axis=1), label='alive')
                plt.plot(t,np.sum(track_data['status']==track_data['particle_status_flags']['dead'],axis=1),label='dead')
                plt.plot(t, track_data['num_part_released_so_far'], label='released')
                plt.ylabel('Number of part.')
                plt.ylabel('Recorded time step')
                plt.legend()
                plt.show()




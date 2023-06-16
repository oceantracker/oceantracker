from os import path, mkdir, getcwd , system
import argparse
import glob
import matplotlib.pyplot as plt
from matplotlib import colors
from oceantracker.util import json_util
from oceantracker.util import time_util
from oceantracker.post_processing.read_output_files import load_output_files
from oceantracker import main
from oceantracker.post_processing.plotting import plot_statistics,plot_tracks, plot_vertical_tracks, plot_utilities
import make_demo_plots
import build_and_test_demos
import numpy as np
from oceantracker.post_processing.read_output_files import load_output_files


    
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

    test_demo=70
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
            demo_name = params['output_file_base']
            if params['reader'] is not None:
                params['reader']['input_dir'] = path.join(path.dirname(__file__), 'demo_hindcast')
            params['root_output_dir'] = 'output'
            output_folder = path.join(params['root_output_dir'], params['output_file_base'])


        if not args.skiprun:
            case_info_file_name, has_errors = main.run(params)

            errors= any(has_errors) if type(has_errors) == list else has_errors
            if errors:
                print('Error during demo')
                exit()
            if type(params) is list:  continue
        # no plotting // cases
        else:
            case_info_file_name =path.join('output', params['output_file_base'],params['output_file_base']+'_caseInfo.json')

        caseInfo = load_output_files.read_case_info_file(case_info_file_name)

        anim= None
        fps=15

        if args.noplot:
            output_file_base= None
        else:
            output_file_base = path.join('output', params['output_file_base'])

        if  args.noplot : continue

        if args.testing:
            #tracks=load_output_files.load_particle_track_vars(case_info_file_name)
            #from oceantracker.post_processing.plotting.plot_utilities import display_grid
            #display_grid(tracks['grid'],ginput=3)
            pass

        plot_output_file = output_file_base if args.save_plot else None


        # do plots
        if 0 < n < 90:

            getattr(make_demo_plots,demo_name)(case_info_file_name, plot_output_file)

        elif n> 0:
            ax_lims = [1591000, 1601500, 5478500, 5491000]
            # have run forwards now backwards from last location
            plt.clf()
            ax= plt.gca()
            d90 = load_output_files.load_particle_track_vars(case_info_file_name)
            plot_utilities.draw_base_map(d90['grid'], ax=ax, show_grid=True, axis_lims=ax_lims,
                                         #title='Back tracking, forward=Green, back=Red', text1='start=Green dot, 1 day- 1 min time steps'
                                         )

            ax.plot(d90['x'][:, :, 0], d90['x'][:, :, 1], color='g', linewidth=3)
            ax.scatter(d90['x'][0, :, 0], d90['x'][0, :, 1], color='g', marker='o', s=20, zorder=9)

            # rerun backwards from end point of forwards run
            start_date = str(time_util.seconds_to_datetime64(d90['time'][-1]))

            params['output_file_base'] = 'Demo90backward'
            params['backtracking'] = True
            params['release_groups']['P1'].update({ 'points': d90['x'][-1, :, :], 'release_start_date': start_date})

            print('backtracking start', start_date)

            caseInfoFile2, has_errors = main.run(params)
            d2 = load_output_files.load_particle_track_vars(caseInfoFile2)

            ax.plot(d2['x'][:, :, 0], d2['x'][:, :, 1], color='y', linewidth=1,linestyle='dashed')
            ax.scatter(d2['x'][0, :, 0], d2['x'][0, :, 1], color='y', marker='o', s=20, zorder=9)
            ax.set_title('Test particle tracking forwards then backwards')
            plt.gcf().tight_layout()
            plot_utilities.show_output(plot_file_name= 'output\\'+ demo_name +'_and_backward_tracks.jpeg')

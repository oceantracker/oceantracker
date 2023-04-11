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


def mfn(movie_file, n=None):
    if movie_file is not None:
        if n is None:
            return movie_file + '.mp4'
        else:
            return movie_file + '_' + str(n) + '.mp4' if args.mp4 else None
    else:
        return None
    
if __name__ == "__main__":
    # run demos from build json files

    parser = argparse.ArgumentParser()
    parser.add_argument('-noplot', action='store_true')
    parser.add_argument('-skiprun', action='store_true')
    parser.add_argument('--demo', default=None, type= int)
    parser.add_argument('--root_output_dir', default='output', type=str)
    parser.add_argument('-mp4', action='store_true')
    parser.add_argument('-testing', action='store_true')
    args = parser.parse_args()


    build_and_test_demos.build_demos()


    if args.root_output_dir is None:  args.root_output_dir = getcwd()

    if not path.isdir(args.root_output_dir):  mkdir(args.root_output_dir)

    demo_dir = path.dirname(__file__)
    json_dir = path.join(demo_dir, 'demo_json')

    if args.demo is None:
        # build full list of   demos
        demo_list=[]
        demofiles = glob.glob(path.join(json_dir, 'demo*.json'))
        for f in demofiles:
            demo_list.append(int(path.split(f)[1][4:6]))
        demo_list.sort()
    else:
        demo_list=[args.demo]

    test_demo=70
    if  args.testing:
        demo_list=[test_demo] # ros ver
    else:
        # get rid of d deveopmenrt demos
        demo_list2=[]
        for d in demo_list:
            if d != test_demo : demo_list2.append((d))
        demo_list= demo_list2

    for n in demo_list:

        f=glob.glob(path.join(json_dir, 'demo' + '%02.0f' % n + '*.json'))
        if len(f)==0:
            exit('runOTdemos.py: No demo file number ' + str(n))

        params = json_util.read_JSON(f[0])

        demo_name= params['shared_params']['output_file_base']
        params['reader']['input_dir'] = path.join(path.dirname(__file__),'demo_hindcast')

        # tests or development choices of classes
        if args.testing:
            pass
            params['reader'].update({'input_dir': 'F:\Hindcasts\Hindcast_samples_tests\ROMS_samples',
                                   'file_mask': 'DopAnV2R3-ini2007_da_his.nc',})
            #params['base_case_params'].update({'interpolator': {'class_name': 'oceantracker.interpolator.scatch_tests.vertical_walk_at_particle_location_interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid'}})
            #params['base_case_params']['dispersion'].update({'A_V':0., 'A_H':0.})
            #params['base_case_params']['particle_release_groups'][0]['pulse_size']=1



        # clean output folder
        params['shared_params']['root_output_dir'] = 'output'
        output_folder = path.join(params['shared_params']['root_output_dir'], params['shared_params']['output_file_base'])

        if not args.skiprun:
            runInfo_file_name, has_errors = main.run(params)

            if has_errors:
                print('Error during demo')
                exit()

        runInfo_file_name = path.join( params['shared_params']['root_output_dir'],params['shared_params']['output_file_base'],params['shared_params']['output_file_base']+'_runInfo.json')
        case_info_file_name = load_output_files.get_case_info_file_from_run_file(runInfo_file_name)
        caseInfo = load_output_files.read_case_info_file(case_info_file_name)

        anim= None
        fps=15

        if args.noplot:
            output_file_base= None
        else:
            output_file_base = path.join('output', params['shared_params']['output_file_base'])

        if  args.noplot : continue

        if args.testing:
            #tracks=load_output_files.load_particle_track_vars(case_info_file_name)
            #from oceantracker.post_processing.plotting.plot_utilities import display_grid
            #display_grid(tracks['grid'],ginput=3)
            pass


        # do plots
        if n <90:
            getattr(make_demo_plots,demo_name)(runInfo_file_name,output_file_base)

        else:
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

            params['shared_params']['output_file_base'] = 'Demo90backward'
            params['shared_params']['backtracking'] = True
            params['base_case_params']['particle_release_groups'][0].update({
                'points': d90['x'][-1, :, :],
                'release_start_date': start_date})

            print('backtracking start', start_date)

            runInfo_file_name2, has_errors = main.run(params)

            caseInfoFile2 = load_output_files.get_case_info_file_from_run_file(runInfo_file_name2)
            d2 = load_output_files.load_particle_track_vars(caseInfoFile2)

            ax.plot(d2['x'][:, :, 0], d2['x'][:, :, 1], color='y', linewidth=1,linestyle='dashed')
            ax.scatter(d2['x'][0, :, 0], d2['x'][0, :, 1], color='y', marker='o', s=20, zorder=9)
            ax.set_title('Test particle tracking forwards then backwards')
            plt.gcf().tight_layout()
            plot_utilities.show_output(plot_file_name= 'output\\'+ demo_name +'_and_backward_tracks.jpeg')

from os import path, mkdir, getcwd , system
import argparse
import glob
import matplotlib.pyplot as plt
from matplotlib import colors
from oceantracker.util import json_util
from oceantracker.util import time_util
from oceantracker.post_processing.read_output_files import load_output_files
from oceantracker import main
from oceantracker.post_processing.plotting import plot_heat_maps,plot_tracks, plot_vertical_tracks, plot_utilities
import build_demo_plots

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
    parser.add_argument('-build', action='store_true')

    args = parser.parse_args()

    if args.build:
        # build json and yamls
        system('python build_and_test_demos.py')

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
        
    for n in demo_list:

        f=glob.glob(path.join(json_dir, 'demo' + '%02.0f' % n + '*.json'))
        if len(f)==0:
            exit('runOTdemos.py: No demo file number ' + str(n))

        params = json_util.read_JSON(f[0])
        demo_name= params['shared_params']['output_file_base']

        # clean output folder
        params['shared_params']['root_output_dir'] = 'output'
        output_folder = path.join(params['shared_params']['root_output_dir'], params['shared_params']['output_file_base'])

        if not args.skiprun:
            runInfo_file_name, has_errors = main.run(params)

            if has_errors:
                print('Error during demo')
                exit()

        case_info_file_name = load_output_files.get_case_info_file_from_run_file(runInfo_file_name)
        caseInfo = load_output_files.read_case_info_file(case_info_file_name)

        anim= None
        fps=15

        if args.noplot:
            output_file_base= None
        else:
            output_file_base = path.join('output', params['shared_params']['output_file_base'])

        if  args.noplot : continue


        # do plots
        if n <90:
            getattr(build_demo_plots,demo_name)(runInfo_file_name,output_file_base)

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
            start_date = time_util.seconds_to_iso8601str(d90['time'][-1])

            params['shared_params']['output_file_base'] = 'Demo90backward'
            params['shared_params']['backtracking'] = True
            params['base_case_params']['particle_release_groups'][0].update({
                'points': d90['x'][-1, :, :],
                'release_start_date': start_date})

            print('backtracking start', start_date)

            runInfo_file_name2, has_errors = main.run(params)

            caseInfoFile2 = load_output_files.get_case_info_file_from_run_file(runInfo_file_name2)
            d2 = load_output_files.load_particle_track_vars(caseInfoFile2)

            ax.plot(d2['x'][:, :, 0], d2['x'][:, :, 1], color='r', linewidth=1.5)
            ax.set_title('Test particle tracking forwards then backwards')
            plt.gcf().tight_layout()
            plot_utilities.show_output(plot_file_name= 'output\\'+ demo_name +'_and_backward_tracks.jpeg')

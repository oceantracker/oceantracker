from os import path, system
from subprocess import Popen, call
import glob
import sys
import argparse


import yaml


if __name__ == "__main__":


    clmaster= ['run_oceantracker.py',' --param_file *dir*\\demo01_plot_tracks.*ext*', ' --input_dir demo_hindcast', ' --root_output_dir output', ' --duration 36000.']

    s='_________________________________________________________________________________________________________________________'
    # run ets with json and ymal file input params
    for file_type, file_dir in zip(['yaml', 'json'],['demo_yaml', 'demo_json']):
        cl=clmaster.copy()
        print( s)
        print( file_type +' parameter file')
        cl[1]= cl[1].replace('*ext*',file_type)
        cl[1]= cl[1].replace('*dir*',file_dir)

        print('test running with command line "python ' + ''.join(cl) +'"' )
        print(s)

        cl[0] ='..\\oceantracker\\' + cl[0]
        system(sys.executable + ' '+ ''.join((cl)))

        system(sys.executable + ' ' + cl[0] +' -h')

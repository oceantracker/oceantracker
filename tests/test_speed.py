# do spreed tests, with fine grid, or external data sets
import test_base
import argparse
import numpy as np
import time
from oceantracker.util import json_util, basic_util
import matplotlib.pyplot as plt,matplotlib.ticker as ticker
from copy import copy, deepcopy
from os import path
from datetime import datetime

def get_file_times(runInfoFile):

    r=json_util.read_JSON(runInfoFile)

    d={}
    d['solver']=r['times']['solver']['total_model_all']['time']
    d['find_cells_and_weights']=r['times']['field_group_manager']['interpolator']['find_cells_and_weights']['time']
    d['eval_interp'] = r['times']['field_group_manager']['interpolator']['find_cells_and_weights']['time']
    d['intialize_hindcast_reader'] = r['times']['field_group_manager']['reader']['intialize_hindcast_reader']['time']
    d['read_hindcast'] = r['times']['field_group_manager']['reader']['read_hindcast']['time']

    log=json_util.read_JSON(ot.solver_ptr.get_full_file_name())

    n=log['run_info']['average_active_particles']

    # get time per time step
    nt= log['run_info']['timesteps_completed']
    RK=log['run_info']['RK_order']
    d2={}
    for key in d:
        d2[key+'_nSecPerRKstep']= 1E09*d[key]/n/nt/RK
    d.update(d2)
    d['particles']=n
    d['time_steps']=nt

    d['nRK']=RK
    d['computer']=r['run_info']['computer']
    return d
if __name__ == '__main__':

    # windows/linux  data source

    parser = argparse.ArgumentParser()
    parser.add_argument('-sounds',action='store_true')
    parser.add_argument('-norun', action='store_true')

    d = [1.0E30]

    args = parser.parse_args()



    params =test_base.base_param(is3D=False)
    basecase=params['base_case_params']
    basecase['dispersion'].update( {'A_H': 0.1})
    basecase['solver'].update( {'screen_output_step_count': 24*3})
    basecase['run_params'].update({'write_tracks': False})
    pgr=basecase['particle_release_groups']
    pgr.pop(0)  # only use polygon release
    pgr[0].update({'release_interval': 0})

    if args.sounds:
        params['reader']={'class_name': 'oceantracker.reader.schism_reader.SCHSIMreaderNCDF',
                          'time_buffer_size':12,
                                'file_mask': 'schism_marl200801*.nc',
                                 'input_dir': 'G:\\Hindcasts_large\\MalbroughSounds_10year_benPhD\\2008',
               }
        poly_points = [[1597682.1237, 5489972.7479],
                   [1598604.1667, 5490275.5488],
                   [1598886.4247, 5489464.0424],
                   [1597917.3387, 5489000],
                   [1597300, 5489000], [1597682.1237, 5489972.7479]]
        basecase['particle_release_groups'][0].update({'points': poly_points})
        params['shared_params'].update({'output_file_base': 'sounds_speed',})

    w={'cpu':np.asarray( [1,2, 3,4,6, 10, 15, 20,25]),#[1, 2, 4, 10, 15, 20, 25],# ,
       'particles':np.asarray([5*10**4,10**5,5*10**5]),#[10**3,10**4,10**5,10**6],#,
       'nSecPerpartPerRKsubstep':[],
       'run_info':[]}
    w['computer'] = basic_util.get_computer_info()


    te= np.full((w['particles'].shape[0],w['cpu'].shape[0]),0.)
    nfile=0
    params['shared_params']['root_output_dir']='F:\\OceanTrackerOuput\\speedTests'
    for n, n_part in enumerate( w['particles'].tolist()):
        for nc, cpu in enumerate(w['cpu'].tolist() ):
            p= deepcopy(params)
            nfile += 1
            p['shared_params']['output_file_base'] += str(nfile)
            t0 = time.perf_counter()

            basecase['particle_release_groups'][0].update({'pulse_size': n_part})

            del p['base_case_params']['particle_release_groups']
            p['case_list']=[]
            for nr in range(cpu) :
                p['case_list'].append({'particle_release_groups' : basecase['particle_release_groups']})

            p['shared_params'].update({'processors': cpu })

            if not args.norun:
                runInfoFile = test_base.run_test(p)

            runInfo_file_name = path.join(p['shared_params']['root_output_dir'], p['shared_params']['output_file_base'], p['shared_params']['output_file_base'] + '_runInfo.json')

            runInfo=json_util.read_JSON(runInfo_file_name)
            te[n,nc]=runInfo['performance']['particles_processed_per_second']

    tn = te/1e06

    lab=['50k particles','100k particles','500k particles']
    ax= plt.gca()
    for n in range(tn.shape[0]):
        ax.plot(w['cpu'],tn[n,:], label=lab[n], zorder=5)
    ax.plot(w['cpu'], tn[-1, 0] * w['cpu'], '--', color=[.8, .8, .8], label='Linear scaling', zorder=3)

    plt.xlabel('Processors')
    plt.ylabel('Speed, million particles per second')

    ax.legend()
    plt.grid(ls='-',color=[.9,.9,.9])
    plt.axis([1, 25, 0, 30])

    if args.sounds:
        plt.title('Large grid')
        plt.text(-.075, 1.075, 'b)', transform=ax.transAxes)
    else:
        plt.title('Small demo. grid')
        plt.text(-.075,1.075, 'a)', transform=ax.transAxes)
    plt.show()


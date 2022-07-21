# do spreed tests, with fine grid, or external data sets
import test_base
import argparse
import numpy as np
import time
from oceantracker.util import basic_util
import matplotlib.pyplot as plt,matplotlib.ticker as ticker

def get_file_times(ot):

    r=json_util.read_JSON(ot.solver_ptr.get_full_file_name())

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
    parser.add_argument('--file_dir', nargs='?', const=0, type=int, default=0)
    parser.add_argument('--size', nargs='?', const=0, type=int, default=0)
    parser.add_argument('--testList', nargs='?', const=None, type=int, default=None,)
    parser.add_argument('-doplot', action='store_true')
    parser.add_argument('-is3D', action='store_true')
    parser.add_argument('--cpu', nargs='?', const=1, type=int, default=1)

    args = parser.parse_args()


# large size grid
    args.size = 3
    args.file_dir = 1
    args.cpu = 1

    paramsWorking= {'dispersion': {'A_H': 0.1},
                    'solver': {'duration': 2.,'screen_output_step_count': 24*3},
                    'particle_group_manager':{'release_interval': 0},
                    'tracks_writer': {'class_name': 'oceantracker.tracks_writer.writerBase.BaseWriter'}  # a non-writer
                    }

    nt=1
    if nt==0:
        # one cpu

        ot = test_base.run_test(args, params=paramsWorking)  # dummy run to compile numba
        r = {}
        for n in [1000,2500,5000,10000,25000,100000, 250000]:
            t0 = time.perf_counter()
            paramsWorking['particle']['pulse_size']=n
            ot = test_base.run_test(args, params=paramsWorking )
            d=get_file_times(ot)

            te=time.perf_counter()-t0
            # gather results into lists
            for key in d:
                if key not in r: r[key]=[]
                r[key].append(d[key])

        plt.subplot(2, 2, 1)
        x=np.array(r['particles'])
        gca=plt.gca()
        gca.plot(x, 1.0e9/np.array(r['solver_nSecPerRKstep']))
        gca.set_xscale('log')

        plt.subplot(2, 2, 2)
        gca = plt.gca()
        gca.plot(x, 1.0e9/np.array(r['find_cells_and_weights_nSecPerRKstep']))
        gca.set_xscale('log')
        plt.show()
        plt.savefig(ot.log_file + '_particles.png', format='png')

    elif nt==1:


        w={'cpu':[1, 2, 4, 10, 15, 20, 25],# [1, 2, 4],
           'particles':[10**3,10**4,10**5,10**6],#,[250]
           'nSecPerpartPerRKsubstep':[],
           'run_info':[]}
        w['computer'] = basic_util.get_computer_info()
        for n_part in w['particles']:
            paramsWorking['write_log_file'] = True
            paramsWorking['particle']['pulse_size'] =int(n_part/4)# 4 release points

            T=[]
            R=[]
            for cpu in w['cpu'] :

                args.cpu=cpu
                t0 = time.perf_counter()

                paramsWorking['write_log_file'] = True if cpu == 1 else False

                ot = test_base.run_test(args, params=paramsWorking)

                if cpu==1:
                    d=get_file_times(ot)
                    T.append(d['solver_nSecPerRKstep'])
                else:

                    d=json_util.read_JSON(ot.parallel_log_file)
                    T.append(d['nSecPerpartPerRKsubstep'])

                R.append(ot.run_info)

            # Form ncpu by case particle lists
            w['run_info'].append(R)
            w['nSecPerpartPerRKsubstep'].append(T)


        plt.subplot(1, 1, 1)
        ax = plt.gca()
        for p,s in zip(w['particles'],w['nSecPerpartPerRKsubstep']):
            ax.plot(w['cpu'], 1e09/np.array(s),label='Particles per core %3.1e' % p)


        ax.legend()
        ax.set_xlabel('CPUs')
        ax.set_ylabel('Particle time steps per sec')
        ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%0.0f'))

        #lab = 'Benchmark_AMD_32_2020_08_25_BCwalkBCordsOutputByRef'
        lab = ''
        ax.set_title('Oceantracker 0.2 '+lab,fontsize= 8)



        plt.savefig(ot.parallel_log_file + '_' + lab + '_cpu.png', format='png')
        #plt.show()

        w['label']=lab


        json_util.write_JSON(ot.parallel_log_file+ lab ,w)




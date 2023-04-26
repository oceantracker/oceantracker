import argparse
import traceback
from oceantracker.util import basic_util
from oceantracker.main import run
from copy import deepcopy

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--test', default=None, type=int)
    args = parser.parse_args()

    #params_that_work= json_util.read_JSON('../demos/demo_param_files/demo05_parallel.json')
    #params_that_work = json_util.read_JSON('../demos/demo_param_files/demo02_animation.json')
    params_that_work = json_util.read_JSON('../demos/demo_param_files/demo56_SCHISM_3D_resupend_crtitical_friction_vel.json')

    params_that_work['shared_params']['max_duration']=3600
    params_that_work['case_list']=[]

    for n in range(12) if args.test is None else  [args.test] :
        p = deepcopy(params_that_work)
        lab=''
        if n==1:
            # spurios params check
            lab='spurious params'
            p['base_case_params']['event_loggers'][0]['polygon_list'][0]['spur1']=1
            p['spur2'] =3
            p['case_list'].append({'spur3': 3})
            p['base_case_params']['event_loggers'][0]['polygon_list'][0]['user_polygonID']=1.
            p['base_case_params']['event_loggers'][0]['polygon_list'][0]['points']=[[1.,]]

        if n == 2:
            lab = 'bad output  folder'
            #p.pop('shared_params')
            p['shared_params']['root_output_dir'] = 'ss:\\test'

        if n==3:
            lab='bad hindcast folder'
            p['reader'].pop('input_dir')
            p['reader']['input_dir']='\\badfolder'
            #['particle_release_groups'][0].pop('points')

        elif n ==4 :
            lab = 'particle_release_groups empty'
            p['base_case_params']['particle_release_groups'] =[]

        if n == 5:
            lab = 'value errors'
            p['base_case_params']['event_loggers'][0]['polygon_list'][0].pop('points')
            p['shared_params']['processors'] = 0
            p['base_case_params']['solver']['n_sub_steps'] = 1.

            p['base_case_params']['solver']['RK_order'] = 0
        if n == 6:
            lab = 'reader value error'
            p['reader']['isodate_of_hindcast_time_zero'] = '70-02-02'
            del p['reader']['file_mask']
        elif n == 7:
            lab = 'reader no file mask'


        print('test:', str(n) , lab,   '---------------------------\n')

        try:
            runInfo_file_name, has_errors = run(p)
        except:
            tb = traceback.format_exc()
            print(tb)




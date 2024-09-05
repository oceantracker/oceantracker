from oceantracker import main
from oceantracker.util import json_util
from os import  path

ncase=2

match ncase:
    case 1:
        fn = r'E:\H_Local_drive\ParticleTracking\bug_hunting\remy\bluff_bug.json'
        params = json_util.read_JSON(fn)
        hindcast_dir = r'F:\Hindcasts\Hindcast_samples_tests\remy_bluff_2023'
        params['reader'].update(dict(input_dir=hindcast_dir ),
                                hgrid_file_name= path.join(hindcast_dir,'hgrid.gr3'),
                                #file_mask= 'schout_29.nc'
                                )
        params['root_output_dir'] = r'F:\OceanTrackerOtuput\bug_hunting'
        params['output_file_base'] += '_remy_bluff'
        del params['release_groups']['clay']['custom_release']
        params['resuspension']['critical_friction_velocity'] = params['resuspension']['critical_friction_velocity'][0]
        #params['shared_params']['processors'] = 1
    case 2:
        params = json_util.read_JSON(r'F:\OceanTrackerOutput\bug_hunting\LCS_oceantracker_traj_outputs\test.json')
        params['root_output_dir'] = r'F:\OceanTrackerOutput\bug_hunting\LCS_oceantracker_traj_outputs'
        params['output_file_base'] = r'test01'

if __name__ == '__main__':

    main.run(params)



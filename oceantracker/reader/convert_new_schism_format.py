import numpy as np
from os import path, makedirs
import pathlib
from oceantracker.util.ncdf_util import NetCDFhandler



def convert(input_dir,output_dir):
    # convet schims out put from new version 5 to old format , as tempoary step to adapting ocean tracker to rewa
    # get list of grid files
    file_list = []
    for fn in pathlib.Path(input_dir).rglob('out2D*.nc'):
        file_list.append(path.abspath(fn))
    pass

    if not path.exists(output_dir):
        makedirs(output_dir)


    for f in file_list:
        file_dir = path.dirname(f)
        file_name= path.basename(f)


        sub_dir =path.join(output_dir, file_dir.split(input_dir)[-1].replace('\\',''))
        if not path.exists(sub_dir):
            makedirs(sub_dir)

        file_ending =file_name.split('_')[-1]
        new_file = path.join(output_dir, sub_dir ,'schout_'+ file_ending)
        single_file= NetCDFhandler(new_file,mode='w')

        # copy grid and 2D variables and attributes
        nc_out = NetCDFhandler(f)

        print('outvars',nc_out.all_var_names())

        ll=['time',
             'minimum_depth',
             'SCHISM_hgrid_node_x',
             'SCHISM_hgrid_node_y',
             'depth',

             'SCHISM_hgrid_face_nodes',
             'SCHISM_hgrid_edge_nodes']

        for l in ll:
            copy_variable(nc_out, single_file, l, l)
        copy_variable(nc_out, single_file,'bottom_index_node','node_bottom_index')
        copy_variable(nc_out, single_file, 'dryFlagElement', 'wetdry_elem')

        copy_variable(nc_out, single_file, 'elevation', 'elev') # tide


        # 2D vectors
        for new_var,vars  in dict(wind_stress=['windStressX','windStressY'],
                                  bottom_stress=['bottomStressX', 'bottomStressY'],
                                  dahv=['depthAverageVelX', 'depthAverageVelY'],
                                  ).items():
            if nc_out.is_var(vars[0]):
                v1 = nc_out.file_handle[vars[0]]
                v2 = nc_out.file_handle[vars[1]]
                data = np.stack((v1,v2),axis=2)
                single_file.write_a_new_variable(new_var, data, nc_out.all_var_dims(vars[0]) + ['two'], attributes=nc_out.all_var_attr(vars[0]))

        # 3d 2D vector water velocity
        fn1= path.join(file_dir,'horizontalVelX_'+ file_ending)
        if path.isfile(fn1):
            v= []
            for l in ['X','Y']:
                fn = path.join(file_dir, 'horizontalVel' +l +'_' + file_ending)
                nc = NetCDFhandler(fn, mode='r')
                v_name= 'horizontalVel' +l
                v.append(nc.file_handle[v_name][:])
                a = nc.all_var_attr(v_name)
                d = nc.all_var_dims(v_name)
                nc.close()
            hvel = np.stack(v,axis=3)
            single_file.write_a_new_variable('hvel', hvel, d + ['two'], attributes=a)

        # 3D scalar variables
        for new_var, var in dict(salt='salinity',
                                 temp='temperature',
                                 vertical_velocity= 'verticalVelocity',
                                 diffusivity= 'diffusivity',
                                 mixing_length=  'mixingLength',
                                 viscosity='viscosity',
                                 TKE= 'turbulentKineticEner',
                                 zcor = 'zCoordinates'
                                 ).items():

            fn= path.join(file_dir,var +'_'+ file_ending)
            if path.isfile(fn):
                nc = NetCDFhandler( fn, mode='r')
                single_file.write_a_new_variable(new_var, nc.file_handle[var], nc.all_var_dims(var), attributes=nc.all_var_attr(var))
                nc.close()
            pass

        single_file.close()

def copy_variable(nc_old,nc_new, old_var,new_var):

        # make sure dims are in new file
        nc_new.write_a_new_variable(new_var,nc_old.file_handle[old_var], nc_old.all_var_dims(old_var), attributes= nc_old.all_var_attr(old_var))


if __name__ == "__main__":
    # test conversion
    input_dir= r'F:\Hindcasts\Hindcast_samples_tests\Auckland_uni_hauarki\new_format'
    output_dir= r'F:\Hindcasts\Hindcast_samples_tests\Auckland_uni_hauarki\new_converted_to_old_ format'

    convert(input_dir,output_dir)

    # test run file


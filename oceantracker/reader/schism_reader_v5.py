from oceantracker.reader.schism_reader import SCHISMreaderNCDF
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC
from pathlib import Path as pathlib_Path
from oceantracker.util.ncdf_util import NetCDFhandler
from os import  path
import numpy as np
from copy import  deepcopy, copy
from glob import  glob
class SCHISMreaderNCDFv5(SCHISMreaderNCDF):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params({
            'grid_variable_map': {'time': PVC('time', str),
                                  'x': PLC(['SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y'], [str], fixed_len=2),
                                  'zlevel': PVC('zCoordinates', str),
                                  'triangles': PVC('SCHISM_hgrid_face_nodes', str),
                                  'bottom_cell_index': PVC('bottom_index_node', str),
                                  'is_dry_cell': PVC('dryFlagElement', np.int8, doc_str='Time variable flag of when cell is dry, 1= is dry cell')},
            'field_variable_map': {'water_velocity': PLC(['horizontalVelX','horizontalVelY', 'verticalVelocity'], [str], fixed_len=2),
                                   'tide': PVC('elevation', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_depth': PVC('depth', str, doc_str='maps standard internal field name to file variable name'),
                                   'water_temperature': PVC('temp', str, doc_str='maps standard internal field name to file variable name'),
                                   'salinity': PVC('salt', str, doc_str='maps standard internal field name to file variable name'),
                                   'wind_stress': PVC('wind_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   'bottom_stress': PVC('bottom_stress', str, doc_str='maps standard internal field name to file variable name'),
                                   'A_Z_profile': PVC('diffusivity', str, doc_str='maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files'),
                                   'water_velocity_depth_averaged': PLC(['dahv'], [str], fixed_len=2,
                                                                        doc_str='maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available')
                                   },
                        })
        self.remove_default_params([ 'file_mask'])


    def get_file_list(self):
        params = self.params
        file_list = []
        for fn in pathlib_Path(params['input_dir']).rglob('*.nc'):
            if 'out2d' in path.basename(fn).lower(): file_list.append(path.abspath(fn))

        if len(file_list) == 0:
            # try using given mask , as may data al in one file
            file_list = super(SCHISMreaderNCDFv5,self).get_file_list()

        return file_list

    def is_file_format(self,file_name):
        # check if file matches this file format
        nc = NetCDFhandler(file_name,'r')
        is_file_type= nc.is_var('SCHISM_hgrid_node_x') and nc.is_var('elevation')
        nc.close()
        return is_file_type

    def is_hindcast3D(self, nc):
        # look for x velocity associated with out2d.nc file
        vel_x_file_name =self.get_3D_var_file_name(nc,self.params['field_variable_map']['water_velocity'][0])
        return vel_x_file_name is not None
    def get_3D_var_file_name(self,nc, var_file_name):
        # get file name matching variable name

        file_var_map= {}
        for fn in glob(path.join(path.dirname(nc.file_name),'*_' + path.basename(nc.file_name).split('_')[1])):
            key =  path.basename(fn).split('_')[0]
            file_var_map[key] = fn
        return  file_var_map[var_file_name] if var_file_name in file_var_map else None

    def setup_water_velocity(self, nc,grid):
        # tweak to be depth avearged
        fm = self.params['field_variable_map']
        var_file_name= self.get_3D_var_file_name(nc,fm['water_velocity'][0])

        if var_file_name is not None:
            #  3D velocity, check if vertical vel file exits
            if self.get_3D_var_file_name(nc,fm['water_velocity'][2]) is not None:
                # drop vertical velocity varaible
                fm['water_velocity'] = fm['water_velocity'][:2]
        else:
            # is depth averaged schism run
            #todo donnt have exmaple of this yet to test
            fm['water_velocity'] =fm['water_velocity_depth_averaged']

    def get_field_params(self, nc, name, crumbs=''):
        # work out if feild is 3D ,etc
        si = self.shared_info
        fmap = deepcopy(self.params['field_variable_map'])

        # if no field map given to use given name as field map
        if name not in fmap:  fmap[name] = name

        # make a list so all maps the same
        if type(fmap[name]) != list: fmap[name] = [fmap[name]]

        # get dims from netx cdf
        var_name0 =fmap[name][0]
        if nc.is_var(var_name0):
            # in 2d out file
            var_dim = nc.all_var_dims(var_name0)
        else:
            # look in 3D files
            var_file_name = self.get_3D_var_file_name(nc,var_name0)
            if var_file_name is not None:
                nc_var= NetCDFhandler(var_file_name,mode='r')
                var_dim = nc_var.all_var_dims(var_name0)
                nc_var.close()
            else:
                # cant find variable
                self.msg(f'Schism v5 reader > Cannot find variable{name} mapped to {fmap[name][0]} in file',
                                            fatal_error=True, exit_now=True)
        f_params = dict(time_varying='time' in var_dim,
                        is3D='nSCHISM_vgrid_layers' in var_dim,
                        is_vector= len(fmap[name]) > 1
                        )
        return f_params

    def read_field_var(self, nc, var_file_name, sel=None):
        # read sel time steps of field variable
        if nc.is_var(var_file_name):
            # 2D variable in out2d.nc
            return super().read_field_var(nc, var_file_name, sel=sel)
        else:
            # 3D variable in another file
            fn = self.get_3D_var_file_name(nc, var_file_name)
            nc_var= NetCDFhandler(fn,mode='r')
            data = nc_var.read_a_variable(var_file_name, sel=sel)
            data_dims = nc_var.all_var_dims(var_file_name)
            nc_var.close()
            return data, data_dims


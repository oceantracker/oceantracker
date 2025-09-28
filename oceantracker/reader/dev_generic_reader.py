import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC, ParameterTimeChecker as PTC

from oceantracker.reader._base_all_readers import _BaseReader

from oceantracker.reader._base_unstructured_reader import _BaseUnstructuredReader
from oceantracker.reader._base_structured_reader import _BaseStructuredReader
from copy import deepcopy
from oceantracker.reader.util import  reader_util

from oceantracker.shared_info import shared_info as si

class _BaseGenericReader(_BaseReader):
    development = True
    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params(

            one_based_indices = PVC(None, bool, doc_str='indices in hindcast start at 1, not zero, eg. triangulation nodes start at 1 not zero as in python', is_required=True),
            grid_variable_map = dict(time= PVC('time',str, doc_str='time variable name in file', is_required=True ),
                               x = PVC(None, str,  is_required=True ),
                               y = PVC(None, str, is_required=True),
                               z= PVC(None, str,doc_str=' name of z variable, or sigma grid variable'),
                               sigma= PVC(None, str,doc_str=' name of sigma, 0-1 vetical grid variable') ),
            dimension_map = dict(  time =PVC('time', str, is_required=True),
                            z = PVC(None, str,doc_str='name of dim for vertical layer boundaries'),
                            all_z_dims=PVC([], str, doc_str='name of all vertical dimensions'),
                            vector2D = PVC(None, str),
                            vector3D = PVC(None, str),
                                  ),
            field_variable_map = dict(  water_velocity =PLC(None,str,is_required=True,),
                                        water_depth=PVC(None, str, is_required=True, ),
                                        tide=PVC(None, str ),
                                        ),
           vertical_grid_type=PVC(None,str, doc_str='use to offset times to required times zone', is_required=True, possible_values=si.vertical_grid_types.possible_values()),
             isodate_of_hindcast_time_zero = PTC(None, doc_str='use to offset times to required times zone', is_required=True),
             )
        self.remove_default_params(['variable_signature'])

    def add_hindcast_info(self):
        params = self.params
        info = self. info
        ds_info =  self.dataset.info
        dm = params['dimension_map']
        fvm= params['field_variable_map']
        gm = params['grid_variable_map']

        info['is3D'] = gm['z'] is not None
        if info['is3D']:
            # sort out z dim and vertical grid size
            info['z_dim'] = dm['z']
            info['num_z_interfaces'] = info['dims'][info['z_dim']]
            info['all_z_dims'] = dm['all_z_dims']
            info['vert_grid_type'] = params['vertical_grid_type']

        pass

    def decode_time(self, time):
        # decode xarray variable time
        result = time.data + self.params['isodate_of_hindcast_time_zero'].astype(np.float64)
        return  result

    def build_vertical_grid(self):
        # add time invariant vertical grid variables needed for transformations
        # first values in z axis is the top? so flip
        params = self.params
        grid = self.grid

        if params['vertical_grid_type'] == si.vertical_grid_types.Sigma:
            ds = self.dataset
            grid['sigma_interface']       = 1. + ds.read_variable(params['grid_variable_map']['sigma_interface']).data.astype(np.float32)  # layer boundary fractions reversed from negative valu
        else:
            si.msg_logger.msg('Generic reader under development, currently only works with sigma vertical grids')


        super().build_vertical_grid()

    def read_dry_cell_data(self, nt_index, buffer_index):
        # get dry cells from water depth and tide
        grid = self.grid
        fields = self.fields
        reader_util.set_dry_cell_flag_from_tide(grid['triangles'], fields['tide'].data, fields['water_depth'].data,
                                                si.settings.minimum_total_water_depth, grid['is_dry_cell_buffer'], buffer_index)
        pass

class GenericUnstructuredReader(_BaseGenericReader, _BaseUnstructuredReader):

    def __init__(self):
        super().__init__()  # required in children to get parent defaults and merge with give params
        self.add_default_params( grid_variable_map = dict(triangles= PVC(None,str, doc_str='grid triangle variable', is_required=True ))
                                 )


    def add_hindcast_info(self):
        params = self.params
        info = self. info

        super().add_hindcast_info() # gert base class info

        info['node_dim'] = params['dimension_map']['node']
        info['num_nodes'] = info['dims'][info['node_dim']]

    def read_triangles(self, grid):
        # read nodes in triangles (N by 3) or mix of triangles and quad cells as  (N by 4)
        ds = self.dataset
        gm = self.params['grid_variable_map']

        tri = ds.read_data(gm['triangles'])
        sel = np.isnan(tri)
        tri[sel] = 0
        tri = tri.astype(np.int32)
        tri -= self.params['one_based_indices']

        grid['triangles'] = tri
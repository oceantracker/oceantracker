from oceantracker.fields._base_field import CustomFieldBase
import numpy as np
from numba import njit
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.numba_util import njitOT
from oceantracker.shared_info import shared_info as si

class VerticalGradient(CustomFieldBase):
    '''Add a vertical gradient field of the  "get_grad_of_field_named" param,
    as a custom field named "get_grad_of_field_named_vertical_grad"'
    '''

    def __init__(self):
        super().__init__()
        self.add_default_params({'get_grad_of_field_named': PVC(None, str, is_required=True, doc_str='Name of field to calculate the vertical gradient of'),
                                 # below are not required as acquired from named field
                                 'time_varying': PVC(True, bool),
                                 'requires3D':  PVC(True, bool),
                                 'is3D': PVC(True, bool),
                                 })

    def initial_setup(self,time_buffer_size, reader_info, reader_fields, grid):
        ml = si.msg_logger
        # get fields prop from named field
        params= self.params
        f = reader_fields[params['get_grad_of_field_named']]
        params['time_varying']= f.is_time_varying()
        params['is3D'] = f.is3D()

        super().initial_setup(time_buffer_size, reader_info, reader_fields, grid)  # set up self.data with above params
        pass

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True,)
    def update(self,fields,grid,nt):

        if 'sigma' in grid:
            _calc_field_vert_grad_from_sigma_levels(fields[self.params['get_grad_of_field_named']].data, grid['sigma'],
                                               fields['tide'].data,fields['water_depth'].data,
                                               grid['bottom_cell_index'], si.settings.z0, self.data)
        else:
            # z levels
            _calc_field_vert_grad_from_zlevels(fields[self.params['get_grad_of_field_named']].data,grid['zlevel'],
                                    grid['bottom_cell_index'], si.settings.z0, self.data)

@njitOT
def _calc_field_vert_grad_from_zlevels(field4D,zlevel,bottom_cell_index,z0,gradient_field):

    for nt in range(field4D.shape[0]):
        for node  in  range(field4D.shape[1]):
            for nz in  range(bottom_cell_index[node],field4D.shape[2]-1):
                dz = zlevel[nt,node,nz+1] - zlevel[nt,node,nz]
                if dz > z0:
                    for ncomp in range(field4D.shape[3]):
                        gradient_field[nt, node, nz, ncomp] = (field4D[nt, node, nz+1, ncomp] - field4D[nt, node, nz, ncomp])/dz
                else:
                    gradient_field[nt, node, nz, :] = 0.

                # top cell, assume gradient same as cell below
                gradient_field[nt, node, -1, :] = gradient_field[nt, node, -2, :]

@njitOT
def _calc_field_vert_grad_from_sigma_levels(field4D,sigma, tide, water_depth,bottom_cell_index,z0,gradient_field):

    for nt in range(field4D.shape[0]):
        for node  in  range(field4D.shape[1]):
            twd = abs(tide[nt,node,0,0] +water_depth[0,node,0,0])

            for nz in  range(bottom_cell_index[node],field4D.shape[2]-1):
                dz = (sigma[nz+1] - sigma[nz]) * twd
                if dz < 0.1: dz = 0.1
                if dz > z0:
                    for ncomp in range(field4D.shape[3]):
                        gradient_field[nt, node, nz, ncomp] = (field4D[nt, node, nz+1, ncomp] - field4D[nt, node, nz, ncomp])/dz
                else:
                    gradient_field[nt, node, nz, :] = 0.

                # top cell, assume gradient same as cell below
                gradient_field[nt, node, -1, :] = gradient_field[nt, node, -2, :]

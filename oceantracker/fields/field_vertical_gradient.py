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

    def initial_setup(self, reader_info):
        ml = si.msg_logger
        # get fields prop from named field
        params= self.params

        # get params of filed to take gradient of
        fparams = reader_info['field_info'][params['get_grad_of_field_named']]['params']
        params['time_varying']= fparams['time_varying']
        params['is3D'] = fparams['is3D']

        super().initial_setup(reader_info)  # set up self.data with above params
        pass

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(requires3D=True,)
    def update(self,fields,grid,nt):

        if 'sigma_interface' in grid:
            _calc_field_vert_grad_from_sigma_levels(fields[self.params['get_grad_of_field_named']].data, grid['sigma_interface'],
                                               fields['tide'].data,fields['water_depth'].data,
                                               grid['bottom_interface_index'], si.settings.z0, self.data)
        else:
            # z levels
            _calc_field_vert_grad_from_z_interfaces(fields[self.params['get_grad_of_field_named']].data,grid['z_interface'],
                                    grid['bottom_interface_index'], si.settings.z0, self.data)

@njitOT
def _calc_field_vert_grad_from_z_interfaces(field4D,z_interface,bottom_interface_index,z0,gradient_field):
    # use centered differences in mid-water colum, first order top and bottom
    for nt in range(field4D.shape[0]):
        for node  in  range(field4D.shape[1]):
            nz_bot = bottom_interface_index[node]
            for nz in  range(nz_bot+1,field4D.shape[2]-1):
                dz = z_interface[nt,node,nz+1] - z_interface[nt,node,nz]
                if dz > z0:
                    dz_inv = 1./dz
                    for ncomp in range(field4D.shape[3]):
                        gradient_field[nt, node, nz, ncomp] = (field4D[nt, node, nz+1, ncomp]
                                                             - field4D[nt, node, nz-1, ncomp])*dz_inv
                else:
                    gradient_field[nt, node, nz, :] = 0.

            # top cell/bottom cell use first order diff.
            dz = z_interface[nt, node, -1] - z_interface[nt, node, -2]
            if dz > z0:
                gradient_field[nt, node, -1, :] =(field4D[nt, node, -1, :]- field4D[nt, node, -2  , :]) / dz
            else:
                gradient_field[nt, node, -1, :] = 0.

            dz = z_interface[nt, node, nz_bot+1] - z_interface[nt, node,nz_bot]
            if dz > z0:
                gradient_field[nt, node, nz_bot, :] = (field4D[nt, node, nz_bot+1, :] - field4D[nt, node, nz_bot, :]) / dz
            else:
                gradient_field[nt, node, nz_bot, :] = 0

@njitOT
def _calc_field_vert_grad_from_sigma_levels(field4D,sigma, tide, water_depth,bottom_interface_index,z0,gradient_field):
    # use centered differences in mid-water colum, first order top and bottom
    for nt in range(field4D.shape[0]):
        for node  in  range(field4D.shape[1]):
            twd = abs(tide[nt,node,0,0] +water_depth[0,node,0,0])
            nz_bot = bottom_interface_index[node]
            for nz in  range(nz_bot+1,field4D.shape[2]-1):
                dz = (sigma[nz+1] - sigma[nz]) * twd
                if dz > z0:
                    dz_inv = 1. / dz
                    for ncomp in range(field4D.shape[3]):
                        gradient_field[nt, node, nz, ncomp] = (field4D[nt, node, nz+1, ncomp] -
                                                               field4D[nt, node, nz-1, ncomp])*dz_inv
                else:
                    gradient_field[nt, node, nz, :] = 0.

            # top cell/bottom cell use first order diff.
            dz =  (sigma[-1] - sigma[-2]) * twd
            if dz > z0:
                gradient_field[nt, node, -1, :] = (field4D[nt, node, -1, :] - field4D[nt, node, -2, :]) / dz
            else:
                gradient_field[nt, node, -1, :] = 0.

            dz = (sigma[nz_bot+1] - sigma[nz_bot]) * twd
            if dz > z0:
                gradient_field[nt, node, nz_bot, :] = (field4D[nt, node, nz_bot + 1, :] - field4D[nt, node, nz_bot, :]) / dz
            else:
                gradient_field[nt, node, nz_bot, :] = 0

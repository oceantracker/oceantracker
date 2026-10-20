from oceantracker.fields._base_field import CustomFieldBase
import numpy as np
from numba import njit
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.util.numba_util import njitOT
from oceantracker.shared_info import shared_info as si

class VerticalGradient(CustomFieldBase):
    '''Add a vertical gradient field of the  "get_grad_of_field_named" param,
    as a custom field named "get_grad_of_field_named_vertical_grad"'
    Holds the gradient of each layer, ie. the slope of the named field between the layer's two interfaces,
    stored at the layer's lower interface. This is the exact vertical derivative of the linearly interpolated named field,
    so particles get the value of the layer they are in (is_layer_value=True), without vertical interpolation.
    Interpolating it vertically would give the particle the gradient from about half a layer higher.
    '''

    def __init__(self):
        super().__init__()
        self.add_default_params({'get_grad_of_field_named': PVC(None, str, is_required=True, doc_str='Name of field to calculate the vertical gradient of'),
                                 # below are not required as acquired from named field
                                 'time_varying': PVC(True, bool),
                                 'requires3D':  PVC(True, bool),
                                 'is3D': PVC(True, bool),
                                 'is_layer_value': PVC(True, bool, expert=True,
                                                       doc_str='Gradient is per layer, particles get the value of the layer they are in'),
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
    # gradient of each layer, between its two interfaces, stored at the layer's lower interface
    for nt in range(field4D.shape[0]):
        for node  in  range(field4D.shape[1]):
            for nz in  range(bottom_interface_index[node],field4D.shape[2]-1):
                dz = z_interface[nt,node,nz+1] - z_interface[nt,node,nz]
                if dz > z0:
                    dz_inv = 1./dz
                    for ncomp in range(field4D.shape[3]):
                        gradient_field[nt, node, nz, ncomp] = (field4D[nt, node, nz+1, ncomp] - field4D[nt, node, nz, ncomp])*dz_inv
                else:
                    gradient_field[nt, node, nz, :] = 0.

            # top interface is not the bottom of a layer, so is never used, give it the top layer's value
            gradient_field[nt, node, -1, :] = gradient_field[nt, node, -2, :]

@njitOT
def _calc_field_vert_grad_from_sigma_levels(field4D,sigma, tide, water_depth,bottom_interface_index,z0,gradient_field):
    # gradient of each layer, between its two interfaces, stored at the layer's lower interface
    for nt in range(field4D.shape[0]):
        for node  in  range(field4D.shape[1]):
            twd = abs(tide[nt,node,0,0] +water_depth[0,node,0,0])
            for nz in  range(bottom_interface_index[node],field4D.shape[2]-1):
                dz = (sigma[nz+1] - sigma[nz]) * twd
                if dz > z0:
                    dz_inv = 1. / dz
                    for ncomp in range(field4D.shape[3]):
                        gradient_field[nt, node, nz, ncomp] = (field4D[nt, node, nz+1, ncomp] - field4D[nt, node, nz, ncomp])*dz_inv
                else:
                    gradient_field[nt, node, nz, :] = 0.

            # top interface is not the bottom of a layer, so is never used, give it the top layer's value
            gradient_field[nt, node, -1, :] = gradient_field[nt, node, -2, :]

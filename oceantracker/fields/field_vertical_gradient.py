from oceantracker.fields._base_field import UserFieldBase
import numpy as np
from numba import njit
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC

class VerticalGradient(UserFieldBase):

    def __init__(self):
        super().__init__()
        self.add_default_params({'name': PVC(None, str, is_required=True) ,
                                 'name_of_field': PVC('', str, is_required=True),
                                 # below are not required as acquired from named field
                                 'is_time_varying': PVC(True, bool, is_required=False),
                                 'is3D': PVC(True, bool, is_required=False),
                                 'num_components': PVC(None, int, is_required=False)
                                 })
        self.class_doc(description='Calculated vertical gradient of "name_of_field" param, as  "name_of_field_vertical_grad"')

    def initialize(self):
        si = self.shared_info
        # get fields prop from named field

        named_field= si.classes['fields'][self.params['name_of_field']]
        self.params.update({'is_time_varying': named_field.params['is_time_varying'],
                            'is_time_varying': named_field.params['is_time_varying'],
                            'is3D':True})

        super().initialize()  # set up self.data with above params
        a=1

    def check_requirements(self):
        msg_list = self.check_class_required_fields_prop_etc(requires3D=True,required_grid_var_list=['bottom_cell_index','zlevel'],
                                    required_fields_list=[self.params['name_of_field']])
        return msg_list


    def update(self,active):
        si = self.shared_info
        fields= si.classes['fields']
        grid= si.classes['reader'].grid
        grid_time_buffers = si.classes['reader'].grid_time_buffers

        _calc_field_vert_grad(fields[self.params['name_of_field']].data,grid_time_buffers['zlevel'],
                                    grid['bottom_cell_index'], si.z0, fields[self.params['name']].data)
@njit
def _calc_field_vert_grad(feild4D,zlevel,bottom_cell_index,z0,gradient_field):

    for nt in range(feild4D.shape[0]):
        for node  in  range(feild4D.shape[1]):
            for nz in  range(bottom_cell_index[node],feild4D.shape[2]-1):
                dz = zlevel[nt,node,nz+1] - zlevel[nt,node,nz]
                if dz > z0:
                    for ncomp in range(feild4D.shape[3]):
                        gradient_field[nt, node, nz, ncomp] = (feild4D[nt, node, nz+1, ncomp] - feild4D[nt, node, nz, ncomp])/dz
                else:
                    gradient_field[nt, node, nz, :] = 0.

                # top cell, assume gradient same as cell below
                gradient_field[nt, node, -1, :] = gradient_field[nt, node, -2, :]



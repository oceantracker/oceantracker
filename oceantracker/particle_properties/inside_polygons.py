from oceantracker.particle_properties._base_properties import ParticleProperty
import numpy as np
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.polygon_util import set_up_list_of_polygon_instances, InsidePolygon
from oceantracker.common_info_default_param_dict_templates import default_polygon_dict_params

class InsidePolygonsNonOverlapping2D(ParticleProperty):
    # property giving ID of 2D polygon which particle is inside. -1 if in no polygon
    # assumes non-overlapping polygons, ie so only inside one at a time, ie the first it is found inside,
    # does not check if polygons overlap
    def __init__(self):
        super().__init__()
        self.add_default_params({'name': PVC('inside_polygons_non_overlapping', str) ,
                                 'initial_value': PVC(-1, int),
                                 'dtype':PVC(np.int32,type)})

        self.class_doc(description= 'Index of polygon a particle is inside',)

        self.add_default_params({'polygon_list':PLC([], [dict], default_value=default_polygon_dict_params,
                                                    can_be_empty_list=False)
                                 })

    def check_requirements(self):
        msg_list = self.check_class_required_fields_prop_etc(required_props_list=['x'])
        return msg_list

    def initialize(self,**kwargs):
        super().initialize()
        si= self.shared_info
        # set up polygons instances

        self.polygons, msg = set_up_list_of_polygon_instances(self.params['polygon_list'])
        si.case_log.add_messages(msg)

    def update(self, active):
        # find polygon each particle is inside
        part_prop = self.shared_info.classes['particle_properties']

        # make all inside no polygon
        self.set_values(-1, active)

        # loop over polygons
        # faster if those already found to be inside previously polygon are eliminated
        to_search = active # for first polygon search all those IDs which are active

        for n, poly in enumerate(self.polygons):
            # assumes non-overlapping polygons, ie so only inside one at a time, the first polygon it is inside
            inside, out_side = poly.inside_indices(part_prop['x'].dataInBufferPtr(), active=to_search, out=self.get_particle_index_buffer(),
                                         also_return_indices_outside=True, out_outside=self.get_particle_subset_buffer())
            self.set_values(n, inside)
            to_search = out_side # on next polygon only search those not in this polygon


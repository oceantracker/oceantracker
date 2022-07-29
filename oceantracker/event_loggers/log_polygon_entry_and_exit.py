from oceantracker.event_loggers._base_event_loggers import _BaseEventLogger
import numpy as np
from oceantracker.util.parameter_checking import  ParamDictValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.common_info_default_param_dict_templates import default_polygon_dict_params
from oceantracker.util.message_and_error_logging import FatalError

class LogPolygonEntryAndExit(_BaseEventLogger):
    # assumes non over lapping polygons

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({'polygon_list': PLC([], [dict], can_be_empty_list=False,
                                                     default_value= default_polygon_dict_params),
                                    'case_output_file_tag': PVC('inside_polygon_events',str)
                                                            })

    def check_requirements(self):
        msg_list = self.check_class_required_fields_properties_grid_vars_and_3D(required_props=['event_polygon', 'current_polygon_for_event_logging'])
        return msg_list


    def initialize(self):

        super().initialize()  # set up using regular grid for  stats
        si = self.shared_info
        if self.instanceID > 0 :
            raise FatalError('LogPolygonEntryAndExit: can only have one instance')

        # add particle property to show which polygon particle is in, -1 = in no polygon
        particle = self.shared_info.classes['particle_group_manager']
        particle.create_particle_property('manual_update',dict(name='event_polygon',  initial_value=-1, dtype=np.int16))
        particle.create_particle_property('user',dict(name='current_polygon_for_event_logging',
                                               class_name= 'oceantracker.particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D',
                                               polygon_list=self.params['polygon_list'],
                                                write=False))

        # set up output file to also write event polygon property
        self.set_up_output_file(['event_polygon'] )

    def update(self,**kwargs):

        part_prop = self.shared_info.classes['particle_properties']

        # find where polygon number has changed due to entry or exit
        IDs_event_began, IDs_event_ended = self.find_events( part_prop['current_polygon_for_event_logging'].dataInBufferPtr() >= 0)

        # for new arrivals in polygon, note the polygon ID
        part_prop['event_polygon'].copy_prop('current_polygon_for_event_logging', IDs_event_began)

        # note those exiting reatin their polygon ID for write
        if self.params['write']:
            self.write_events(IDs_event_began, IDs_event_ended)

        # now updates written change polygon ID to no polygon for those exiting
        part_prop['event_polygon'].set_values(-1, IDs_event_ended)
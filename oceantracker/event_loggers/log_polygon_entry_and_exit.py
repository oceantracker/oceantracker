from oceantracker.event_loggers._base_event_loggers import _BaseEventLogger
import numpy as np
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterListChecker as PLC

from oceantracker.particle_properties.util import particle_operations_util
from oceantracker.shared_info import shared_info as si

class LogPolygonEntryAndExit(_BaseEventLogger):
    # assumes non over lapping polygons

    def __init__(self):
        super().__init__()
        # set up info/attributes
        self.add_default_params({'polygon_list': PLC(si.default_polygon_dict_params, dict, is_required=True),
                                    'role_output_file_tag': PVC('inside_polygon_events',str)
                                                            })

    def check_requirements(self):
       self.check_class_required_fields_prop_etc(required_props_list=['event_polygon', 'current_polygon_for_event_logging'])

    def add_required_classes_and_settings(self, settings, reader_builder, msg_logger):
        super().add_required_classes_and_settings(settings, reader_builder, msg_logger)
        info = self.info
        si.add_class('particle_properties', class_name='ManuallyUpdatedParticleProperty', name='event_polygon', initial_value=-1, dtype='int16')
        si.add_class('particle_properties', name='current_polygon_for_event_logging',
                     class_name='oceantracker.particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D',
                     polygon_list=self.params['polygon_list'], write=False)

    def initial_setup(self):
        super().initial_setup()  # set up using regular grid for  stats
        # add particle property to show which polygon particle is in, -1 = in no polygon


        ml = si.msg_logger
        if self.info['instanceID'] > 0 :
            #todo why only 1
            ml.msg('LogPolygonEntryAndExit: can only have one instance',fatal_error=True,exit_now=True )



        # set up output file to also write event polygon property
        self.set_up_output_file(['event_polygon'] )

    def update(self,n_time_step, time_sec):
        self.start_update_timer()

        part_prop = si.class_roles.particle_properties
        event_polygon = part_prop['event_polygon']
        current_polygon_for_event_logging = part_prop['current_polygon_for_event_logging']

        # find where polygon number has changed due to entry or exit
        IDs_event_began, IDs_event_ended = self.find_events(current_polygon_for_event_logging.used_buffer() >= 0)

        # for new arrivals in polygon, note the polygon ID
        particle_operations_util.copy(event_polygon.data, current_polygon_for_event_logging.data, IDs_event_began)


        # note those exiting reatin their polygon ID for write
        if self.params['write']:
            self.write_events(IDs_event_began, IDs_event_ended)

        # now updates written change polygon ID to no polygon for those exiting
        event_polygon.set_values(-1, IDs_event_ended)

        self.stop_update_timer()
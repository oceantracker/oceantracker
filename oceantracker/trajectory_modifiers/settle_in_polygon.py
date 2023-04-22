import numpy as np
from  oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC
from oceantracker.util.polygon_util import  InsidePolygon

class SettleInPolygon(_BaseTrajectoryModifier):
    # fallows particles to freeze if inside a polygon
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC('settle_in_polygon', str),
                                 'polygon': {'points': PVC(None,'vector', is_required=True)},
                                 'probability_of_settlement': PVC(0.,float),
                                 'settlement_duration': PVC(0., float),  #  time block stranding after stranding has occured
                                 })
        self.polygons = []

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['is_frozen_in_polygon', 'time_of_settlement', 'status'])



    def initialize(self, **kwargs):

        super().initialize()
        si=self.shared_info

        # set up polygons to test if particles inside
        if 'points' not in self.params['polygon']:
            si.msg_logger.msg('initialize: Polygon settlement, each polygon must be a dictionary with at least a "points"  key a list of corrdinates', fatal_error=True)

        a = np.asarray(self.params['polygon']['points'])
        if a.shape[1] != 2:
            raise Exception('initialize: parameter polygon_ points must be a list of lists of cordinate pairs, eg [[p1_x1,p1_y1],[p1_x2,p1_y2],..]]')

        self.polygon = InsidePolygon(verticies=a)# do set up to speed inside using pre-calculation

        # add particle prop to track which are inside polygon, which will be automatically written to output
        particle= si.classes['particle_group_manager']
        particle.create_particle_property( 'manual_update',dict(name='is_frozen_in_polygon', dtype=np.int8))

        # ad a parameter to record when last released
        particle.create_particle_property('manual_update',dict(name='time_of_settlement',  initial_value=0.))

    # all particles checked to see if they need status changing
    def update(self, time_sec, active):
        si = self.shared_info
        part_prop = si.classes['particle_properties']

        # find those inside and freeze, only if they haven't been recently frozen
        those_inside = self.polygon.inside_indices(part_prop['x'].used_buffer(), out= self.get_particle_index_buffer(), active=active)
        if those_inside.shape[0] > 0:

            not_frozen = part_prop['status'].find_subset_where(those_inside, 'eq', si.particle_status_flags['moving'])
            rand = np.random.rand(not_frozen.shape[0])
            settling = not_frozen[rand < self.params['probability_of_settlement']]
            part_prop['status'].set_values(si.particle_status_flags['frozen'], settling)
            part_prop['is_frozen_in_polygon'].set_values(1, settling)
            part_prop['time_of_settlement'].set_values(time_sec, settling)

        # now look at all those frozen
        frozen = part_prop['status'].compare_all_to_a_value( 'eq', si.particle_status_flags['frozen'], out=self.get_particle_index_buffer())
        time_settled = np.abs(time_sec - part_prop['time_of_settlement'].get_values(frozen)) # abs works even if backtracking
        release =  frozen[ time_settled > self.params['settlement_duration'] ]
        part_prop['status'].set_values(si.particle_status_flags['moving'], release)
        part_prop['is_frozen_in_polygon'].set_values(0, release)
        part_prop['time_of_settlement'].set_values(0, release)
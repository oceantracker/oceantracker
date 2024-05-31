import numpy as np
from oceantracker.util.parameter_checking import ParamValueChecker as PVC,ParameterListChecker as PLC,ParameterTimeChecker as PTC
from oceantracker.trajectory_modifiers._base_trajectory_modifers import BaseTrajectoryModifier
from oceantracker.particle_properties.util import particle_comparisons_util
from oceantracker.util.basic_util import IDmapToArray
from oceantracker.util.numba_util import njitOT

from oceantracker.shared_info import SharedInfo as si


class CullParticles(BaseTrajectoryModifier):
    '''
    Prototype for how to  cull particles,
    this version just culls random particles of given statuses,
     at given interval and start end times.

    To give other behaviors inherit and change "def select_particles_to_cull(self, time_sec, active):" method')
    '''
    #todo add scheduler
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults

        self.add_default_params(
                start =PTC(None,doc_str='start date/time of first cull" '),
                end =  PTC(None,doc_str='date/time of last cull'),
                interval= PVC( None, float, min=0,doc_str='time in seconds between culls, default 1 day'),
                statuses= PLC(['moving', 'on_bottom', 'stranded_by_tide', 'stationary'], str, min_len=1,
                              doc_str='list of status names to cull ', possible_values=si.particle_status_flags.possible_values()),
                probability=PVC(1.0, float, min=0, max=1.),

                # obsolete
                cull_status_greater_than=PVC(None,str,obsolete='Use param "statuses"  '),
                cull_status_equal_to= PVC(None,str,obsolete='Use param "statuses"  '),
                                  )

    def initial_setup(self):

        super().initial_setup()  # set up
        params= self.params

        # use time step to cull in none given
        if params['interval'] is None or params['interval'] == 0:
            params['interval']= si.settings.time_step

        si.add_scheduler_to_class('culler01',self,interval=params['interval'],
                                  start=params['start'],
                                  end=params['start'])
        self.statuses_to_cull= IDmapToArray(si.particle_status_flags,params['statuses'])

    def check_requirements(self):
        self.check_class_required_fields_prop_etc(required_props_list=['x', 'status'])

    def select_particles_to_cull(self, time_sec, active):
         
        part_prop = si.roles.particle_properties
        eligible_to_cull = self._cullIDs(part_prop['status'].used_buffer(), self.statuses_to_cull,
                                       self.get_partID_buffer('B1'))
        culled = particle_comparisons_util.random_selection(eligible_to_cull, self.params['probability'], self.get_partID_subset_buffer('B1'))
        #print('xx', self.statuses_to_cull,culled.size)
        return culled

    def update(self,n_time_step, time_sec, active):

        if self.culler01.do_task(n_time_step):
            part_prop =  si.roles.particle_properties
            culled = self.select_particles_to_cull(time_sec, active)
            part_prop['status'].set_values(si.particle_status_flags.dead, culled)

    @staticmethod
    @njitOT
    def _cullIDs(status, statuses, out):

        found = 0
        for n in  range(status.shape[0]):
            for m in range(len(statuses)):
                # check if in array of required status IDs
                if status[n] == statuses[m]:
                    out[found] = n # index matching a
                    found += 1
                    break # is so move on to next
        return out[:found]



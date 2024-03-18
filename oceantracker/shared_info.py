
from oceantracker import common_info_default_param_dict_templates as ci
from oceantracker.util.parameter_checking import merge_params_with_defaults, time_util

from oceantracker.util.messgage_logger import  MessageLogger

from time import  perf_counter
from oceantracker.util import cord_transforms
import numpy as np
from oceantracker.util.scheduler import Scheduler
from oceantracker.particle_properties import particle_operations

class Object(object):
    pass

class SharedInfo(object):
    r"""Gives access to shared variables, classes and some utility methods. Attributes are:

    .classes[role] class instance(s) in given role
    """


    msg_logger = MessageLogger()
    block_timers={}
    classes = {}
    roles = Object()
    particle_operations = particle_operations

    @classmethod
    def setup(self):
        # set up empty class and roles variables for all roles
        self.classes = {}
        #self.roles = Object() # altenative attribute bases class strcture
        for role in ci.core_class_list + ci.class_dicts_list:
            self.classes[role] = None if role in  ci.core_class_list else {}
            #setattr(self.roles, role,  Object())

        # shortcuts???
        self.fgm = self.classes['field_group_manager']
        self.pgm = self.classes['particle_group_manager']
        self.part_prop = self.classes['particle_properties']


    @classmethod
    def add_core_class(self, class_role, params, crumbs ='',initialise=False,default_classID=None):

        ml= self.msg_logger
        crumbs  =crumbs + f' >>> adding core class type >> "{class_role}" '
        if class_role not in ci.core_class_list:
            ml.spell_check(f'Role "{class_role}" is not known', class_role, ci.core_class_list, exit_now=True, crumbs=crumbs)
        # make instance  and merge params
        i = self.class_importer.new_make_class_instance_from_params(params,class_role, default_classID=default_classID, crumbs=crumbs)

        self.classes[class_role] = i
        if initialise: i.initial_setup()

        #if not hasattr(self.roles, class_role): setattr(self.roles, class_role, class_role)
        #setattr(self.roles, class_role, i)
        if initialise: i.initial_setup()
        return i

    @classmethod
    def add_user_class(self, class_role, name = None, params= {}, class_type='user' ,crumbs='', initialise=False, default_classID=None, caller=None):
        ml = self.msg_logger

        crumbs  =crumbs+ f' >>> adding core class type >> "{class_role}.{name}"  '
        if class_role not in ci.class_dicts_list :
            ml.spell_check(f'Role "{class_role}" is not ', class_role, ci.class_dicts_list,
                           crumbs=crumbs, exit_now= True)

        i = self.class_importer.new_make_class_instance_from_params(params, class_role, default_classID=default_classID, crumbs=crumbs)
        i.info['name'] = name
        i.info['type'] = class_type
        i.info['class_role'] = class_role

        #if not hasattr(self.roles,class_role): setattr(self.roles, class_role,Object())
        #setattr(getattr(self.roles, class_role), name, i)
        if name in self.classes[class_role]:
            self.msg_logger.msg('Class type"' + class_role + '" already has a class with name = "' + i.info['name']
                   + '", "name" parameter must be unique',
                   caller=caller, crumbs=crumbs, fatal_error=True)
        else:
            self.classes[class_role][name] = i

        i.info['instanceID'] = len(self.classes[class_role]) -1

        if initialise: i.initial_setup()

        return i

    @classmethod
    def all_class_instance_pointers_iterator(self):
        # build list of all points for iteration, eg in calling all close methods
        p = []

        for name, item in self.classes.items():
           if name in ci.class_dicts_list:
               # set of classes
               if item is not None:
                    for key, i in item.items():
                        if i is not None:  p.append(i)

           else:
                if item is not None:
                    p.append(item)

        return p

    @classmethod
    def block_timer(self,name,t0):
        b = self.block_timers
        if name not in b:
            b[name] = dict(time=0.,calls=0)
        b[name]['time'] += perf_counter()-t0
        b[name]['calls'] += 1

    @classmethod
    def setup_lon_lat_to_meters_grid_tranforms(self,grid_lon_lat):
        #todo add user given meters grid option
        if self.settings['EPSG_code_metres_grid'] is None:
            epsg = cord_transforms.get_utm_epsg(grid_lon_lat)
        else:
            epsg =  self.settings['EPSG_code_metres_grid']

        self.Transformer_to_meters = cord_transforms.get_tansformer(cord_transforms.EPSG_WGS84,epsg)
        self.Transformer_to_lon_lat = cord_transforms.get_tansformer(epsg, cord_transforms.EPSG_WGS84)

    @classmethod
    def transform_lon_lat_to_meters(self, lon_lat, in_lat_lon_order=False, crumbs=''):
        # transform 2D/3D vector of points or single point to meters
        # also swaps input data to lon_lat if in_lat_lon_order
        out= lon_lat.copy() # keep anz z cord

        if lon_lat.ndim==1:
            # single point
            if in_lat_lon_order: lon_lat[0], lon_lat[1] = out[1], out[0]
            out[0], out[1] = self.Transformer_to_meters.transform(lon_lat[ 0], lon_lat[1])
        else:
            # vector of coords
            # swap input columns if inputs are as (lat, lon)  and not (lon,lat)
            if in_lat_lon_order: lon_lat[:, 0], lon_lat[:, 1]  = out[:, 1].copy(), out[:, 0].copy()
            out[:, 0], out[:, 1], = self.Transformer_to_meters.transform(lon_lat[:, 0], lon_lat[:, 1])

        if np.any(~np.isfinite(out.ravel())):
            self.msg_logger.msg('Could not convert some lon_lat to meters, values out of bounds, or values in lat lon order?',
                            crumbs=crumbs,fatal_error=True,exit_now=True)
        return out

    @classmethod
    def transform_lon_lat_deltas(self,ll_deltas, ref_lon_lat,  deltas_in_lat_lon_order=False):
        # transform step in lon lat difereces in meter grid diff   (a 2 element array) at given lat long/3D vector of points or single point to meters


        if deltas_in_lat_lon_order: ll_deltas[0], ll_deltas[1] = ll_deltas[1], ll_deltas[0]

        ll= np.vstack((ref_lon_lat, ref_lon_lat+ll_deltas))

        x, y = self.Transformer_to_meters.transform(ll[:,0], ll[:,1])

        out = np.asarray([float(x[1]-x[0]),float(y[1]-y[0])] )
        return out

    @classmethod
    def add_scheduler_to_class(self, name_scheduler, param_class_instance, start=None, end=None, duration=None,
                               interval =None, times=None,
                               caller=None, crumbs=''):
        ''' Add a scheduler opject to given param_class_instance, with boolean task_flag attribute for each time step,
            which is true if  task is to be carried out.
            Rounds times interval and times to nearest time step'''
        s = Scheduler(self.run_info,self.hindcast_info, start=start, end=end,duration=duration,
                            interval =interval, times=times)
        if s.interval_rounded_to_time_step:
            self.msg_logger.msg('Making scheduler: update interval rounded to be integer number of time steps',
                                hint=f'{interval:.0f} sec. rounded to model time step = {s.info["interval"]:.0f} sec.',
                                caller=param_class_instance, warning=True, crumbs= crumbs+' adding scheduler' )
        # add to the class
        setattr(param_class_instance, name_scheduler, s)
        # add info about scheduler to in
        if not hasattr(param_class_instance,'scheduler_info'): setattr(param_class_instance,'scheduler_info',dict())
        param_class_instance.scheduler_info[name_scheduler] = s.info
        return s

    @classmethod
    def get_regular_events_within_hindcast(self, interval, start=None, end=None, duration=None,
                           crumbs='',caller=None):
      # wrapper to give regular event times within hindcastend

      d = time_util.get_regular_events_within_hindcast(self.hindcast_info, self.run_info,self.msg_logger, interval,
                            start=start,end=end,crumbs=crumbs,caller=caller)
      return d



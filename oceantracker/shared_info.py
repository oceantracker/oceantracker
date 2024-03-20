from typing import TypedDict

from oceantracker import common_info_default_param_dict_templates as ci
from oceantracker.util.parameter_checking import merge_params_with_defaults, time_util

from oceantracker.util.messgage_logger import  MessageLogger

from time import  perf_counter
from oceantracker.util import cord_transforms
import numpy as np
from oceantracker.util.scheduler import Scheduler
from oceantracker.particle_properties import particle_operations


# useful utility classes to enable auto complete
class _Object(object):  pass
class _SharedStruct():
    # holds varives as clas attributes to enable auto complete hints and give iterators over these attributes
    @classmethod
    def as_dict(cls):
        d = dict()
        for key, item in cls.__dict__.items():
            if not key.startswith('_'): d[key] = item
        return d
    @classmethod
    def possible_values(cls):
        d = []
        for key in cls.__dict__.keys():
            if not key.startswith('_'): d.append(key) 
        return d
    @classmethod
    def __getitem__(cls, name:str):
        return getattr(cls,name)

    # blocks that make up parts of shared info
class _ClassRoles(_SharedStruct):
    release_groups = {}
    fields = {}  # user fields calculated from other fields  on reading
    particle_properties =  {} # user added particle properties, eg DistanceTraveled
    velocity_modifiers = {}  # user added velocity effects, eg TerminalVelocity
    trajectory_modifiers = {}  # change particle paths, eg. re-suspension
    particle_statistics = {}  # heat map inside polygon statistics calculated on the fly
    particle_concentrations = {}  # writes concentration of particles and other properties calculated on the fly.   files ,eg PolygonEntryExit
    nested_readers = {}
    event_loggers =  {} # writes events files ,eg PolygonEntryExit
    time_varying_info = {} # particle info,eg. time,or  tide at at tide gauge, core example is particle time

class _CoreClassRoles(_SharedStruct):
    reader = None
    solver = None
    field_group_manager = None
    interpolator = None
    particle_group_manager = None
    tracks_writer = None
    dispersion = None
    tidal_stranding = None
    resuspension = None
    integrated_model = None # this is here as there can be only one at a time

class _ParticleStatusFlags(_SharedStruct):
    '''Particle status flags mapped to integer values'''
    unknown  =-128
    bad_cord = -20
    cell_search_failed=  -19
    notReleased = -10
    dead = -2
    outside_open_boundary =-1
    stationary = 0
    stranded_by_tide = 3
    on_bottom = 6
    moving =  10

class _CellSearchStatusFlags(_SharedStruct):
        ok =0
        outside_domain=1
        blocked_domain=-5
        blocked_dry_cell=-4
        bad_cord=-20
        failed=-30

class _UseFullInfo(_SharedStruct):
    # default reader classes used by auto-detection of file type
    known_readers = {'schisim': 'oceantracker.reader.schism_reader.SCHISMreaderNCDF',
                     'schisim_v5': 'oceantracker.reader.schism_reader_v5.SCHISMreaderNCDFv5',
                     'fvcom': 'oceantracker.reader.FVCOM_reader.unstructured_FVCOM',
                     'roms': 'oceantracker.reader.ROMS_reader.ROMsNativeReader',
                     'delft3d_fm': 'oceantracker.reader.dev_delft_fm.DELFTFM',
                     'generic': 'oceantracker.reader.generic_ncdf_reader.GenericNCDFreader',
                     'dummy_data': 'oceantracker.reader.dummy_data_reader.DummyDataReader',
                     }
    known_prop_types = ['manual_update', 'from_fields', 'user']
    large_float = 1.0E32

# Shared class, build using the above
#------------------------------------------------------------
class SharedInfo(object):
    """Gives access to shared variables, classes and some utility methods. Attributes are:

        eg SharedInfo.particle_properties is a dictionary of named particle property instances

    """
    roles = _ClassRoles
    core_roles = _CoreClassRoles
    particle_operations = particle_operations
    particle_status_flags = _ParticleStatusFlags() # need to be instances to allow particle_status_flags[key] form
    cell_search_status_flags = _CellSearchStatusFlags()

    msg_logger = MessageLogger()
    block_timers={}
    classes = {}
    info = _UseFullInfo

    @classmethod
    def _setup(cls):
        # empty out roles and core roles in case of rerunning and shared info import only happens once
        for role in cls.core_roles.as_dict().keys():
            setattr(cls.core_roles, role, None)
        for role in cls. roles.as_dict().keys():
            setattr(cls.roles,role,{})

        # todo deprecated .classes
        cls.classes = {}
        for role in list(cls. roles.as_dict().keys()) +  list(cls.core_roles.as_dict().keys()):
            cls.classes[role] = None if role in  cls.core_roles.as_dict() else {}


    @classmethod
    def add_core_role(cls, class_role, params, crumbs ='',initialise=False,default_classID=None):

        ml= cls.msg_logger
        crumbs  =crumbs + f' >>> adding core class type >> "{class_role}" '
        if class_role not in ci.core_class_list:
            ml.spell_check(f'Role "{class_role}" is not known', class_role, ci.core_class_list, exit_now=True, crumbs=crumbs)
        # make instance  and merge params
        i = cls.class_importer.new_make_class_instance_from_params(params,class_role, default_classID=default_classID, crumbs=crumbs)
        if initialise: i.initial_setup()

        setattr(cls.core_roles,class_role, i) # add to shared info

        #todo deprecated .classes
        cls.classes[class_role] = i

        return i

    @classmethod
    def add_user_class(cls, class_role, name = None, params= {}, class_type='user' ,crumbs='', initialise=False, default_classID=None, caller=None):
        ml = cls.msg_logger

        crumbs  =crumbs+ f' >>> adding core class type >> "{class_role}.{name}"  '
        if class_role not in ci.class_dicts_list :
            ml.spell_check(f'Role "{class_role}" is not ', class_role, ci.class_dicts_list,
                           crumbs=crumbs, exit_now= True)

        i = cls.class_importer.new_make_class_instance_from_params(params, class_role, default_classID=default_classID, crumbs=crumbs)
        i.info['name'] = name
        i.info['type'] = class_type
        i.info['class_role'] = class_role

        #if not hasattr(cls.roles,class_role): setattr(cls.roles, class_role,Object())
        #setattr(getattr(cls.roles, class_role), name, i)
        if name in cls.classes[class_role]:
            cls.msg_logger.msg('Class type"' + class_role + '" already has a class with name = "' + i.info['name']
                   + '", "name" parameter must be unique',
                   caller=caller, crumbs=crumbs, fatal_error=True)
        else:
            # add to roles dictionary
            getattr(cls.roles, class_role)[name] = i

            # todo deprecated .classes
            cls.classes[class_role][name] = i

        i.info['instanceID'] = len(cls.classes[class_role]) -1

        if initialise: i.initial_setup()

        return i

    @classmethod
    def all_class_instance_pointers_iterator(cls):
        # build list of all points for iteration, eg in calling all close methods
        p = []

        for name, item in cls.classes.items():
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
    def block_timer(cls,name,t0):
        b = cls.block_timers
        if name not in b:
            b[name] = dict(time=0.,calls=0)
        b[name]['time'] += perf_counter()-t0
        b[name]['calls'] += 1

    @classmethod
    def setup_lon_lat_to_meters_grid_tranforms(cls,grid_lon_lat):
        #todo add user given meters grid option
        if cls.settings['EPSG_code_metres_grid'] is None:
            epsg = cord_transforms.get_utm_epsg(grid_lon_lat)
        else:
            epsg =  cls.settings['EPSG_code_metres_grid']

        cls.Transformer_to_meters = cord_transforms.get_tansformer(cord_transforms.EPSG_WGS84,epsg)
        cls.Transformer_to_lon_lat = cord_transforms.get_tansformer(epsg, cord_transforms.EPSG_WGS84)

    @classmethod
    def transform_lon_lat_to_meters(cls, lon_lat, in_lat_lon_order=False, crumbs=''):
        # transform 2D/3D vector of points or single point to meters
        # also swaps input data to lon_lat if in_lat_lon_order
        out= lon_lat.copy() # keep anz z cord

        if lon_lat.ndim==1:
            # single point
            if in_lat_lon_order: lon_lat[0], lon_lat[1] = out[1], out[0]
            out[0], out[1] = cls.Transformer_to_meters.transform(lon_lat[ 0], lon_lat[1])
        else:
            # vector of coords
            # swap input columns if inputs are as (lat, lon)  and not (lon,lat)
            if in_lat_lon_order: lon_lat[:, 0], lon_lat[:, 1]  = out[:, 1].copy(), out[:, 0].copy()
            out[:, 0], out[:, 1], = cls.Transformer_to_meters.transform(lon_lat[:, 0], lon_lat[:, 1])

        if np.any(~np.isfinite(out.ravel())):
            cls.msg_logger.msg('Could not convert some lon_lat to meters, values out of bounds, or values in lat lon order?',
                            crumbs=crumbs,fatal_error=True,exit_now=True)
        return out

    @classmethod
    def transform_lon_lat_deltas(cls,ll_deltas, ref_lon_lat,  deltas_in_lat_lon_order=False):
        # transform step in lon lat difereces in meter grid diff   (a 2 element array) at given lat long/3D vector of points or single point to meters


        if deltas_in_lat_lon_order: ll_deltas[0], ll_deltas[1] = ll_deltas[1], ll_deltas[0]

        ll= np.vstack((ref_lon_lat, ref_lon_lat+ll_deltas))

        x, y = cls.Transformer_to_meters.transform(ll[:,0], ll[:,1])

        out = np.asarray([float(x[1]-x[0]),float(y[1]-y[0])] )
        return out

    @classmethod
    def add_scheduler_to_class(cls, name_scheduler, param_class_instance, start=None, end=None, duration=None,
                               interval =None, times=None,
                               caller=None, crumbs=''):
        ''' Add a scheduler opject to given param_class_instance, with boolean task_flag attribute for each time step,
            which is true if  task is to be carried out.
            Rounds times interval and times to nearest time step'''
        s = Scheduler(cls.run_info,cls.hindcast_info, start=start, end=end,duration=duration,
                            interval =interval, times=times)
        if s.interval_rounded_to_time_step:
            cls.msg_logger.msg('Making scheduler: update interval rounded to be integer number of time steps',
                                hint=f'{interval:.0f} sec. rounded to model time step = {s.info["interval"]:.0f} sec.',
                                caller=param_class_instance, warning=True, crumbs= crumbs+' adding scheduler' )
        # add to the class
        setattr(param_class_instance, name_scheduler, s)
        # add info about scheduler to in
        if not hasattr(param_class_instance,'scheduler_info'): setattr(param_class_instance,'scheduler_info',dict())
        param_class_instance.scheduler_info[name_scheduler] = s.info
        return s

    @classmethod
    def get_regular_events_within_hindcast(cls, interval, start=None, end=None, duration=None,
                           crumbs='',caller=None):
      # wrapper to give regular event times within hindcastend

      d = time_util.get_regular_events_within_hindcast(cls.hindcast_info, cls.run_info,cls.msg_logger, interval,
                            start=start,end=end,crumbs=crumbs,caller=caller)
      return d



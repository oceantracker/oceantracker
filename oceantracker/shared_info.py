from typing import TypedDict

from oceantracker import definitions
from oceantracker.util.parameter_checking import ParameterCoordsChecker as PCC, ParameterListChecker as PLC

from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterTimeChecker as PTC

from oceantracker.util import shared_info_util, class_importer_util, basic_util
from oceantracker.util.messgage_logger import  MessageLogger

from time import  perf_counter
from oceantracker.util import cord_transforms
import numpy as np
from oceantracker.util.scheduler import Scheduler
from oceantracker.particle_properties import particle_operations
from os import path

# useful utility classes to enable auto complete
class _Object(object):  pass
class _SharedStruct():
    '''
    holds variables as clas attributes to enable auto complete hints
    and give iterators over these variables

    allows both  instance.backtracking and i['instance.backtracking']

    '''
    def __init__(self):
        # add  class variables in ._class_.__dict__
        # to instance __dict__ by adding attributes
        for key, item in self.__class__.__dict__.items():
            if not key.startswith('_'):
                setattr(self, key, item)
    def as_dict(self):
        d = dict()
        for key, item in self.__dict__.items():
            if not key.startswith('_'): d[key] = item
        return d

    def possible_values(self):
        d = []
        for key in self.__dict__.keys():
            if not key.startswith('_'): d.append(key) 
        return d

    def __getitem__(self, name:str):
        return getattr(self,name)
    def __setitem__(self, name:str, value):
        setattr(self,name, value)

# default settings structure

class _DefaultSettings(_SharedStruct):

    root_output_dir=  PVC('root_output_dir', str, doc_str='base dir for all output files')
    add_date_to_run_output_dir =  PVC(False,bool, doc_str='Append the date to the output dir. name to help in keeping output from different runs separate' )
    output_file_base =    PVC('output_file_base', str,
                doc_str= 'The start/base of all output files and name of sub-dir of "root_output_dir" where output will be written' )
    time_step = PVC(3600., float, min=0.001, units='sec',doc_str='Time step in seconds for all cases' )
    screen_output_time_interval = PVC(3600., float, doc_str='Time in seconds between writing progress to the screen/log file' )
    backtracking =   PVC(False, bool, doc_str='Run model backwards in time')
    regrid_z_to_uniform_sigma_levels = PVC(True, bool,
                doc_str='much faster 3D runs by re-griding hydo-model fields in the z to uniform sigma levels on read, based on sigma most curve z_level profile. Some hydo-model are already uniform sigma, so this param is ignored, eg ROMS' )
    display_grid_at_start = PVC(False, bool,
                doc_str='Pause during strat up to plot the grid for checking using matplotlib, clicking om image will print a coord' )
    dev_debug_plots = PVC(False, bool,expert=True, doc_str='show any debug plot generated at give dbug_level, not for general use' )
    debug = PVC(False, bool, doc_str= 'more info on errors' )
    dev_debug_opt = PVC(0, int,expert=True,doc_str= 'does extra checks given by integer, not for general use' )
    minimum_total_water_depth = PVC(0.25, float, min=0.0, units='m', doc_str='Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering' )
                #'write_output_files =     PVC(True,  bool, doc_str='Set to False if no output files are to be written, eg. for output sent to web' )
    write_dry_cell_flag = PVC(True, bool,
                doc_str='Write dry cell flag to all cells when writing particle tracks, which can be used to show dry cells on plots,may create large grid file, currently cannot be used with nested grids ' )
    max_run_duration = PVC(definitions.max_timedelta_in_seconds, float,min=.00001,units='sec',doc_str='Maximum duration in seconds of model run, this sets a maximum, useful in testing' )  # limit all cases to this duration
    max_particles = PVC(10**10, int, min=1, doc_str='Maximum number of particles to release, useful to restrict if splitting particles' )  # limit all cases to this number
    processors = PVC(None, int, min=1,doc_str='number of processors used, if > 1 then cases in the case_list to run in parallel' )
    max_warnings = PVC(50,    int, min=0,doc_str='Number of warnings stored and written to output, useful in reducing file size when there are warnings at many time steps' )  # dont record more that this number of warnings, to keep caseInfo.json finite
    use_random_seed = PVC(False,  bool,doc_str='Makes results reproducible, only use for testing developments give the same results!', expert=True )
    NUMBA_function_cache_size = PVC(4048, int, min=128, expert=True,
                                    doc_str='Size of memory cache for compiled numba functions in kB' )
    NUMBA_cache_code = PVC(False, bool, expert=True,
                           doc_str='Speeds start-up by caching complied Numba code on disk in root output dir. Can ignore warning/bug from numba "UserWarning: Inspection disabled for cached code..."' )
    multiprocessing_case_start_delay = PVC(None, float, min=0.,expert=True,
                                           doc_str='Delay start of each sucessive case run parallel, to reduce congestion reading first hydo-model file' )  # which large numbers of case, sometimes locks up at start al reading same file, so ad delay
    EPSG_code_metres_grid = PVC(None, int,
                doc_str='If hydro-model has lon_lat coords, then grid is converted to this meters system. For codes see https://epsg.io/. eg EPSG for NZ Transverse Mercator use 2193. Default grid is UTM' )
    write_tracks = PVC(True, bool, doc_str='Flag if "True" will write particle tracks to disk. For large runs and statistics done on the fly, is normally set to False to reduce output volumes' )
    user_note = PVC('No user note', str, doc_str='Any run note to store in case info file' )
    z0 = PVC(0.005, float, units='m', doc_str='Bottom roughness, used for tolerance and log layer calcs. ', min=0.0001 )  # default bottom roughness
    water_density = PVC(1025., float, units='kg/m^3', doc_str='Water density , default is seawater, an example of use is in calculating friction velocity from bottom stress, ', min=900. )
    open_boundary_type = PVC(0, int, min=0, max=1, doc_str='new- open boundary behaviour, only current option=1 is disable particle, only works if open boundary nodes  can be read or inferred from hydro-model, current schism using hgrid file, and inferred ROMS ' )
    block_dry_cells = PVC(True, bool, doc_str='Block particles moving from wet to dry cells, ie. treat dry cells as if they are part of the lateral boundary' )
    use_A_Z_profile = PVC(True, bool,
                doc_str='Use the hydro-model vertical turbulent diffusivity profiles for vertical random walk (more realistic) instead of constant value (faster), if profiles are in the file' )
    include_dispersion = PVC(True, bool,
                doc_str='Include random walk, allows it to be turned off if needed for applications like Lagrangian coherent structures')
    NCDF_time_chunk = PVC(24, int, min=1,expert=True,
                          doc_str='Used when writing time series to netcdf output, is number of time steps per time chunk in the netcdf file')
    multi_processing_method = PVC('spawn', str, expert=True,possible_values=['fork','spawn'],
                          doc_str='How  mutil procing is implemeted, spawn= separate work spaces, fork = has copy on parents memory space')

        #  #'loops_over_hindcast =  PVC(0, int, min=0 )  #, not implemented yet,  artifically extend run by rerun from hindcast from start, given number of times
        # profiler = PVC('oceantracker', str, possible_values=available_profile_types,
        #                 doc_str='in development- Default oceantracker profiler, writes timings of decorated methods/functions to run/case_info file use of other profilers in development and requires additional installed modules ' )
        # 'debug_level =               PVC(0, int,min=0, max=10, doc_str='Gives  diferent levels of debug, in development' )


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
    unknown  = basic_util.fillvalue('int8')
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
        outside_open_boundary=1
        blocked_domain=-5
        blocked_dry_cell=-4
        bad_cord=-20
        failed=-30


class _RunInfo(_SharedStruct):
    is3D_run = None
    model_direction = None
    free_wheeling = None
    start_time = None
    end_time = None
    current_model_time = None
    current_model_date = None
    current_model_time_step = 0
    times = None
    duration = None
    run_output_dir = None
    output_file_base = None
    caseID = None
    time_of_nominal_first_occurrence = None
    total_alive_particles = 0
    time_steps_completed = 0

class _UseFullInfo(_SharedStruct):
    # default reader classes used by auto-detection of file type

    known_prop_types = ['manual_update', 'from_fields', 'user']
    large_float = 1.0E32



# Shared class, build using the above
#------------------------------------------------------------
class _SharedInfoClass():
    """Gives access to shared variables, classes and some utility methods. Attributes are:

        eg SharedInfo.particle_properties is a dictionary of named particle property instances

    """
    settings = _DefaultSettings() # will be overwritten with actual values by case runner
    roles = _ClassRoles()
    core_roles = _CoreClassRoles()
    particle_operations = particle_operations
    default_settings = _DefaultSettings()
    particle_status_flags = _ParticleStatusFlags() # need to be instances to allow particle_status_flags[key] form
    cell_search_status_flags = _CellSearchStatusFlags()
    run_info  = _RunInfo()
    hindcast_info = None
    msg_logger = MessageLogger()
    block_timers={}
    classes = {}  # todo deprecated
    info = _UseFullInfo

    def __init__(self):

        self.default_polygon_dict_params = {'user_polygonID': PVC(0, int, min=0),
                                       'name': PVC(None, str),
                                       'points': PCC(None, is_required=True, doc_str='Points making up the polygon as, N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array')
                                       }

        pass
    def _setup(self):
        # this allows shared info to make a class importer when needed
        self.msg_logger.set_screen_tag('Prelim')
        self.msg_logger.reset()
        self._class_importer = class_importer_util.ClassImporter(self, self.msg_logger)

        # empty out roles and core roles in case of rerunning and shared info import only happens once
        for role in self.core_roles.as_dict().keys():
            setattr(self.core_roles, role, None)
        for role in self. roles.as_dict().keys():
            setattr(self.roles,role,{})

        # todo deprecated .classes
        self.classes = {}
        for role in list(self.roles.as_dict().keys()) +  list(self.core_roles.as_dict().keys()):
            self.classes[role] = None if role in  self.core_roles.as_dict() else {}



    def add_core_role(self, class_role, params,default_classID=None,initialise=False,
                      caller=None,crumbs =''):

        ml= self.msg_logger
        crumbs  =crumbs + f' >>> adding core class type >> "{class_role}" '
        if class_role not in self.core_roles.possible_values():
            ml.spell_check(f'Role "{class_role}" is not known', class_role,  self.core_roles.possible_values(), exit_now=True, crumbs=crumbs)
        # make instance  and merge params

        i = self.make_instance_from_params(class_role, params,default_classID=default_classID,
                                            crumbs=crumbs, caller = caller, name = None)
        if initialise: i.initial_setup()

        setattr(self.core_roles,class_role, i) # add to shared info
        i.shared_info = self

        #todo deprecated .classes
        self.classes[class_role] = i

        return i

    def add_user_class(self, class_role, name, params,  class_type='user' ,crumbs='', initialise=False, default_classID=None, caller=None):
        ml = self.msg_logger

        crumbs  =crumbs+ f' >>> adding core class type >> "{class_role}.{name}"  '
        if class_role not in self.roles.possible_values():
            ml.spell_check(f'Role "{class_role}" is not ', class_role, self.roles,
                           crumbs=crumbs, exit_now= True)

        i =self.make_instance_from_params( class_role, params, name=name, default_classID=default_classID, crumbs=crumbs)
        i.info['name'] = name
        i.info['type'] = class_type
        i.info['class_role'] = class_role

        #if not hasattr(self.roles,class_role): setattr(self.roles, class_role,Object())
        #setattr(getattr(self.roles, class_role), name, i)
        if name in self.roles[class_role]:
            self.msg_logger.msg('Class type"' + class_role + '" already has a class with name = "' + i.info['name']
                   + '", "name" parameter must be unique',
                   caller=caller, crumbs=crumbs, fatal_error=True)
        else:
            # add to roles dictionary
            getattr(self.roles, class_role)[name] = i

            # todo deprecated .classes
            self.classes[class_role][name] = i

        i.info['instanceID'] = len(self.classes[class_role]) -1
        i.shared_info = self

        if initialise: i.initial_setup()

        return i

    def add_release_group_instance(self, name=None, **kwargs):
        '''Add a release group with given name as an instance to computational pipeline, not the same as add_class, which just adds parameters'''
        pgm= self.core_roles.particle_group_manager
        i = pgm. add_release_group(name,kwargs)
        return i
    def make_instance_from_params(self, class_role,params,  name = None, default_classID=None,
                               caller=None, crumbs=''):

        i = self._class_importer.new_make_class_instance_from_params(
                    class_role, params, default_classID=default_classID,
                    name = name, crumbs=crumbs,caller=caller)
        return  i
    def _all_class_instance_pointers_iterator(self):
        # build list of all points for iteration, eg in calling all close methods
        p = []
        for role in self.core_roles.possible_values():
            i = getattr(self.core_roles,role)
            if i is not None: p.append(i)

        for role in self.roles.possible_values():
            r = getattr(self.roles, role)
            if r is not None:
                for key, i in r.items():
                    if i is not None:  p.append(i)
        return p

    def block_timer(self,name,t0):
        b = self.block_timers
        if name not in b:
            b[name] = dict(time=0.,calls=0)
        b[name]['time'] += perf_counter()-t0
        b[name]['calls'] += 1

    def _setup_lon_lat_to_meters_grid_tranforms(self,grid_lon_lat):
        #todo add user given meters grid option
        if self.settings['EPSG_code_metres_grid'] is None:
            epsg = cord_transforms.get_utm_epsg(grid_lon_lat)
        else:
            epsg =  self.settings['EPSG_code_metres_grid']

        self.Transformer_to_meters = cord_transforms.get_tansformer(cord_transforms.EPSG_WGS84,epsg)
        self.Transformer_to_lon_lat = cord_transforms.get_tansformer(epsg, cord_transforms.EPSG_WGS84)

    def _transform_lon_lat_to_meters(self, lon_lat, in_lat_lon_order=False, crumbs=''):
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

    def _transform_lon_lat_deltas(self,ll_deltas, ref_lon_lat,  deltas_in_lat_lon_order=False):
        # transform step in lon lat difereces in meter grid diff   (a 2 element array) at given lat long/3D vector of points or single point to meters


        if deltas_in_lat_lon_order: ll_deltas[0], ll_deltas[1] = ll_deltas[1], ll_deltas[0]

        ll= np.vstack((ref_lon_lat, ref_lon_lat+ll_deltas))

        x, y = self.Transformer_to_meters.transform(ll[:,0], ll[:,1])

        out = np.asarray([float(x[1]-x[0]),float(y[1]-y[0])] )
        return out

    def add_scheduler_to_class(self, name_scheduler, param_class_instance, start=None, end=None, duration=None,
                               interval =None, times=None,
                               caller=None, crumbs=''):
        ''' Add a scheduler object to given param_class_instance, with boolean task_flag attribute for each time step,
            which is true if  task is to be carried out.
            Rounds times interval and times to nearest time step'''
        s = Scheduler(self.settings,self.run_info,self.hindcast_info, start=start, end=end,duration=duration,
                            interval =interval, times=times,
                      caller=caller,msg_logger=self.msg_logger,
                      crumbs=crumbs + '> adding scheduler')
    # add to the class
        setattr(param_class_instance, name_scheduler, s)
        # add info about scheduler to in
        if not hasattr(param_class_instance,'scheduler_info'): setattr(param_class_instance,'scheduler_info',dict())
        param_class_instance.scheduler_info[name_scheduler] = s.info
        return s



# make the instance used throughout code
SharedInfo = _SharedInfoClass()
pass
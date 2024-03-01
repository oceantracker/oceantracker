
from oceantracker import common_info_default_param_dict_templates as common_info
from oceantracker.util.parameter_checking import merge_params_with_defaults
from time import  perf_counter
from oceantracker.util import cord_transforms
import numpy as np
class SharedInfoClass(object):
    # allows working classes access to instances of other classes to use their methods
    def __init__(self):
        self.reset()
        self.block_timers={}
        self.classes ={}

    def reset(self):
        self.classes = {}
        # fill in known user class and iterator names
        for key in common_info.class_dicts_list:
            self.classes[key] = {}

    def add_core_class(self, class_role, params, crumbs ='',initialise=False,default_classID=None):

        ml= self.msg_logger
        crumb_base = f' >>> adding core class type >> "{class_role}" '

        # make instance  and merge params
        i = self.class_importer.new_make_class_instance_from_params(params,class_role, default_classID=default_classID, crumbs=crumb_base + crumbs)

        self.classes[class_role] = i
        if initialise: i.initial_setup()
        return i

    def create_class_dict_instance(self,name,class_role, group, params,  crumbs='', initialise=False,default_classID=None):
        # dynamically  get instance of class from string eg oceantracker.solver.Solver
        ml= self.msg_logger

        instanceID = len(self.classes[class_role])

        crumb_base = f' >>> adding_class type >> "{class_role}"  (name=  "{name}" instance #{instanceID: 1d}), '

        # make instance  and merge params
        i = self.class_importer.new_make_class_instance_from_params(params,class_role,name=name,crumbs=crumb_base + crumbs, default_classID=default_classID)

        if class_role not in common_info.class_dicts_list :
            ml.msg(f'Class type = "{class_role}": name is not a known class_role=' + class_role ,
                   exception = True, crumbs =  crumb_base + crumbs)

        # now add to class lists and interators

        i.info['type'] = group

        # needed for release group identification info etc, zero based
        i.info['instanceID'] =  instanceID

        i.info['class_role'] = class_role

        if name in self.classes[class_role]:
            ml.msg('Class type"' + class_role + '" already has a class with name = "' + i.info['name']
                         + '", "name" parameter must be unique',  crumbs =crumb_base + crumbs,  fatal_error=True)
        else:
            self.classes[class_role][name] = i
        if initialise: i.initial_setup()
        return i

    def all_class_instance_pointers_iterator(self):
        # build list of all points for iteration, eg in calling all close methods
        p = []

        for name, item in self.classes.items():
           if name in common_info.class_dicts_list:
               # set of classes
               if item is not None:
                    for key, i in item.items():
                        if i is not None:  p.append(i)

           else:
                if item is not None:
                    p.append(item)

        return p

    def block_timer(self,name,t0):
        b = self.block_timers
        if name not in b:
            b[name] = dict(time=0.,calls=0)
        b[name]['time'] += perf_counter()-t0
        b[name]['calls'] += 1

    def setup_lon_lat_to_meters_grid_tranforms(self,grid_lon_lat):
        #todo add user given meters grid option
        if self.settings['EPSG_code_metres_grid']:
            epsg = cord_transforms.get_utm_epsg(grid_lon_lat)
        else:
            epsg =  self.settings['EPSG_code_metres_grid']

        self.Transformer_to_meters = cord_transforms.get_tansformer(cord_transforms.EPSG_WGS84,epsg)
        self.Transformer_to_lon_lat = cord_transforms.get_tansformer(epsg, cord_transforms.EPSG_WGS84)


    def transform_lon_lat_to_meters(self, lon_lat, in_lat_lon_order=False):
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

        return out

    def transform_lon_lat_deltas(self,ll_deltas, ref_lon_lat,  deltas_in_lat_lon_order=False):
        # transform step in lon lat difereces in meter grid diff   (a 2 element array) at given lat long/3D vector of points or single point to meters


        if deltas_in_lat_lon_order: ll_deltas[0], ll_deltas[1] = ll_deltas[1], ll_deltas[0]

        ll= np.vstack((ref_lon_lat, ref_lon_lat+ll_deltas))

        x, y = self.Transformer_to_meters.transform(ll[:,0], ll[:,1])

        out = np.asarray([float(x[1]-x[0]),float(y[1]-y[0])] )
        return out

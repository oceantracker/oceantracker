from copy import deepcopy, copy

from inspect import getfullargspec
from dataclasses import  dataclass, field
from _datetime import datetime
from typing import List, ClassVar
import numpy as np
from oceantracker.util import  time_util, basic_util

crumb_seperator= ' >> '

def merge_params_with_defaults(params, default_params, msg_logger, crumbs= '',
                              caller=None, check_for_unknown_keys=True):
    # merge nested parameters with defaults,
     # default dict. items must be one of 3 types
    # 1)  ParamDictValueChecker class instance
    # 2)   ParamDictListChecker class instance
    # crumbs is a string giving crumb trail to this parameter, for messaging purposes
    crumbs += ' > merge_params_with_defaults'
    if params is None : params ={}
    if type(params) not in[dict, int] :
        msg_logger.msg('Params must be a dictionary or list of parameter dict,  got type=' + str(type(params)),
                       crumbs=crumbs,caller=caller,fatal_error= True)
        return params
    if type(default_params) != dict:
        msg_logger.msg(f'Default_params must be a dictionary,  got type={str(type(default_params))}',
                       crumbs=crumbs,caller=caller,fatal_error= True)
        return params

    # find which keys/params are obsolete and the remainder
    obsolute_params = [key for key, item in default_params.items() if isinstance(item, _ParameterBaseDataClassChecker) and item.obsolete]
    possible_params = [key for key, item in default_params.items() if key  not in obsolute_params]

    # first check if any keys in base or case params are not in defaults
    # allow pass on those starting with #
    if check_for_unknown_keys:
        for key in list(params.keys()):
            msg = f'Parameter "{key}"'
            if  key not in default_params and not key.startswith('#'):
                # get possible values without obsolete params
                msg_logger.spell_check(msg, key,possible_params,caller=caller,
                           crumbs= crumbs + crumb_seperator + f'"{key}"', fatal_error=True)
            elif key in obsolute_params:
               msg_logger.msg(msg + ' is obsolete',
                              hint=default_params[key].doc_str,
                              fatal_error=True, crumbs=crumbs, caller=caller)

    # loop over non-obsolete default keys
    for key in possible_params:
        item = default_params[key]
        msg =f'Parameter "{key}"'
        parent_crumb = f'{msg}, in {crumbs}{crumb_seperator}"{key}"'

        if key not in params: params[key] = None  # add Noe /not given if not present

        if isinstance(item,_ParameterBaseDataClassChecker):
            params[key] = item.get_value(key, params[key], msg_logger, parent_crumb, caller)

        elif type(item) == dict:
            # nested param dict
            params[key] = merge_params_with_defaults(params[key], item,   msg_logger, crumbs=parent_crumb + crumb_seperator + key)

        elif type(item) == list:
            # a nested list of  param dict
            for n in enumerate(item):
                item[n] = merge_params_with_defaults(params[key], item[n], msg_logger, crumbs=parent_crumb + crumb_seperator + key)
        else:
            msg_logger.msg(f'{msg},merge_params_with_defaults items in default dictionary can be ParamDictValueChecker, ParameterListChecker, or a nested param dict',
                           crumbs= parent_crumb,fatal_error = True, caller=caller)
    return params

@dataclass
class _ParameterBaseDataClassChecker():
    default: field(default=None, metadata={"required": True})

    def __post_init__(self):
        pass
    def get_default(self):
        return self.default

    def asdict(self): return self.__dict__

    def get_value(self, key, user_param, msg_logger, crumbs, caller):
        # get value from ParamDictValueChecker after basic checks
        crumbs = f'{crumbs} {crumb_seperator} {key} '
        # check if trying to set obsolete param
        if user_param is None:
            if self.is_required:
                msg_logger.msg(f'Required parameter: must set parameter "{key}"',
                    hint=f'Variable description:{self.doc_str}', crumbs=crumbs, fatal_error=True, caller=caller)
                return None
            else:
                value = self.get_default()
        else:
            # check the user given value
            value = self.check_value(key, user_param, msg_logger, crumbs, caller)

        return value


# the ecognised types that a parameter can contain
# and what types can be converted to each fundamental type
_fundamental_types= {str:(str,),
                float:(float,int, np.float64,np.float32, np.integer),
                int : (int, np.integer),
                bool: (bool, np.bool_),
                     dict: (dict, ),
                }

_all_convertible_types = tuple([x for x1 in _fundamental_types.values() for x in x1])
#  [x for xs in xss for x in xs]
@dataclass
class ParamValueChecker(_ParameterBaseDataClassChecker):
    data_type: any = None  # must be second
    expert : bool= False
    obsolete: bool = False
    is_required: bool = False
    doc_str : str = None
    units: str = None
    min: float = None
    max: float = None
    possible_values: list = None

    def __post_init__(self):
        super().__post_init__()

        ok = list(_fundamental_types.keys())
        # ensure it is one of known fundamental types that can be checked
        if self.data_type not in ok:
            s= f'Given type "{str(self.data_type)}" is not currently one of  the fundamental paramter checker can work with'
            basic_util.CodingError(s, hint=f'Must be one  of {ok}' ,
                    info=f'class {self.__class__.__name__}(default value, data_type,...)')

        # add information for booleans
        if type(self.default) == bool:
            self.possible_values = [True, False]

        if self.possible_values is not None and type(self.possible_values) != list:
            self.possible_values = [self.possible_values]

    def check_value(self,key, value, msg_logger, crumbs, caller):
        crumbs += '> ParameterValueChecker'
        msg = f'Parameter "{key}"'

        # check type
        if not isinstance(value,_fundamental_types[self.data_type]):
            msg_logger.msg(f'{msg}, is not required data type, got type {type(value)}, value given =  {str(value)}',
                           hint =f'Must be one of types {_fundamental_types[self.data_type]}',
                           caller=caller, fatal_error=True, crumbs=crumbs)
        if self.possible_values is not None and value not in self.possible_values:
            msg_logger.msg(f'{msg}, unexpected value={str(value)}',
                           hint=f'Must be one of {str(self.possible_values)}',
                           caller=caller, fatal_error=True, crumbs=crumbs)
            return None

        if self.data_type == float:  value =  float(value) # make int, np.float64, np.float32 as  floats

        # check max/mins
        if self.data_type in [ float, int]:
            if self.min is not None and value < self.min:
                msg_logger.msg(f'{msg}, value {str(value)} must  be greater than {str(self.min)}', caller=caller, fatal_error=True, crumbs=crumbs)
            if self.max is not None and value > self.max:
                msg_logger.msg(f'{msg}, value {str(value)} must  be less than {str(self.max)}', caller=caller, fatal_error=True, crumbs=crumbs)

        return value

@dataclass
class ParameterTimeChecker(_ParameterBaseDataClassChecker):
    possible_types: List =  field(default_factory=lambda: [str, float, np.datetime64,int, np.float64, np.float32])
    expert : bool= False
    obsolete: bool = False
    is_required: bool = False
    doc_str : str = None
    units: str = 'ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970'
    def check_value(self, key, value, msg_logger, crumbs,  caller):

        crumbs = 'ParameterTimeChecker > ' + crumbs
        msg = f'Parameter "{key}"'
        try:
            if type(value) == str:
                return time_util.isostr_to_seconds(value) # convert iso string
            if type(value) in [int, float,  np.float64, np.float32]:
                return float(value)

            if type(value) == np.datetime64:
                return time_util.datetime64_to_seconds(value)

            #should never get here
            msg_logger.msg(f'{msg }, unexpected value = "{str(value)}", type = "{str(type(value))}"', caller=caller,
                           hint= f'Must be {self.units}',
                           fatal_error=True, crumbs=crumbs)

        except Exception as e:
                msg_logger.msg( f'{msg }, failed to convert to date got value = "{str(value)}", type = "{str(type(value))}"',caller= caller,
                                hint=f'Must be {self.units}', fatal_error=True, crumbs = crumbs)
        pass

@dataclass
class ParameterListChecker(ParamValueChecker):
    # below relate to a list and its contents
    # list must be all teh same fundamental type
    possible_types: List = field(default_factory=lambda: [])

    make_list_unique: bool = False
    fixed_len: int = None
    min_len: int = 0

    def get_default(self):
        return [] if self.default is None else self.default
    def check_value(self,key, values, msg_logger, crumbs, caller):
        # check out elements of list
        crumbs += ' > ParameterListChecker'
        msg = f'Parameter "{key}"'
        pass
        # check length
        if self.fixed_len is not None and len(values) != self.fixed_len:
            msg_logger.msg(f'{msg}, list must be  exactly {self.fixed_len:d} long',
                           hint= f'got list length={len(values) }', crumbs=crumbs,caller=caller)
        if values is not None and len(values) < self.min_len:
            msg_logger.msg(f'{msg}, list must be  at least {self.fixed_len:d} long',
                           hint= f'got list length={len(values) }', crumbs=crumbs,caller=caller)

        # check each value in list and convert to fundamental types in parent checker
        for n, v in enumerate(values):
            values[n] = super().check_value(key, v, msg_logger, crumbs, caller)

        if self.make_list_unique:
            values = list(set(values))

        return values


@dataclass
class ParameterCoordsChecker(_ParameterBaseDataClassChecker):
    possible_types: List =  field(default_factory=lambda: [str, float, np.datetime64,int, np.float64, np.float32])
    expert : bool= False
    obsolete: bool = False
    is_required: bool = False
    doc_str : str = None
    units: str = 'metres, or (lon, lat) as  decimal degrees if hindcast in (lon, lat) '
    one_or_more_points: bool = False
    single_cord: bool = False
    is3D: bool = False
    min: float = None
    max: float = None

    def check_value(self, key, value, msg_logger, crumbs,  caller):

        crumbs = f'ParameterCoordsChecker > ' + crumbs
        msg = f'Parameter "{key}"'

        if type(value) not in [list, np.ndarray]:
            msg_logger.msg(f'{msg}, expected param of type list or numpy array got type {type(value)}',
                           fatal_error=True, caller=caller, crumbs=crumbs)
            return None

        # attempt array conversion
        try:
            value = np.asarray(value)
        except Exception as e:
            msg_logger.msg(f'{msg}, coordinates must be numpy array or a list convertible to a numpy array ',
                           hint = f'got values {str(value)}',caller = caller,
                           crumbs = crumbs, fatal_error=True)


        # now have an array
        if not np.issubdtype(value.dtype, np.integer) and not np.issubdtype(value.dtype, np.floating):
            msg_logger.msg(f'{msg}, coordinates must only contain floats or ints, got type "{str(value.dtype)}" ',
                           hint=f'got values {str(value)}',caller = caller,
                           crumbs=crumbs, fatal_error=True)
            return None

        # make int float
        value= value.astype(np.float64)

        # if one or more expected make 1 by n
        if self.one_or_more_points and value.ndim==1:
            value= value.reshape((1,-1))
            self.single_cord = False

        # now have double array, so check shape
        if self.single_cord:
            # only expecting 2 or 3 cord values
            if value.shape[0] < 2 or value.shape[0] > 3 :
                msg_logger.msg(f'{msg},, expecting coordinates with only 2 or 3 values',
                               hint=f'got values {str(value)}', crumbs=crumbs, fatal_error=True)

            if not self.is3D and value.shape[0] == 3:
                msg_logger.msg(f'{msg}, expecting coordinates as 2D pair of values',
                               hint=f'got values {str(value)}', crumbs=crumbs, fatal_error=True)
            return value

        # must be a vector of coords and expect an N by 2 or 3 array
        if value.ndim == 1:
                msg_logger.msg(f'expecting N by 2 or 3 array, eg. [[2.4,4.5],[6.2,7.8],[6.6,9.]]',
                        hint=f'got values {str(value)}', crumbs=crumbs, fatal_error=True)
                return None

        if value.shape[1] < 2 or value.shape[1] > 3:
            msg_logger.msg(f'Expected and  vector N by 2 or 3 list or numpy array of coordinate pairs or triples, eg [[ 34., 56.]], ',
                   crumbs=crumbs,
                   hint =f'got size "{str(value.shape)}"', fatal_error=True)
            return None

        #check min max
        if self.min is not None and np.any(value< self.min):
            msg_logger.msg(f'{msg}, value {str(value)} must  be greater than {str(self.min)}', caller=caller, fatal_error=True, crumbs=crumbs)
        if self.max is not None and np.any(value > self.max):
            msg_logger.msg(f'{msg}, value {str(value)} must  be less than {str(self.max)}', caller=caller, fatal_error=True, crumbs=crumbs)

        return value

# todo add ListOfParameterDictionaries case for polygon lists etc





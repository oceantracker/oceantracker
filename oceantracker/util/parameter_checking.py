from copy import deepcopy, copy
from oceantracker.util.parameter_checkingV2 import _ParameterBaseDataClassChecker, ParameterValueChecker2, ParameterTimeChecker

import numpy as np
from oceantracker.util import  time_util
from inspect import getfullargspec


crumb_seperator= ' >> '

def merge_params_with_defaults(params, default_params, msg_logger, crumbs= '',
                              caller=None, check_for_unknown_keys=True):
    # merge nested paramteres with defaults, returns a copy of params updated
    # if param key is in base case then use base case rather than value from ParamDictValueChecker.get_default()
    # default dict. items must be one of 3 types
    # 1)  ParamDictValueChecker class instance
    # 2)   ParamDictListChecker class instance
    # crumbs is a string giving crumb trail to this parameter, for messaging purposes

    # merge into a copy of params to leave original unchanged

    if params is None : params ={}

    if type(params) != dict :
        msg_logger.msg('merge_with_defaults, parameter ' + crumbs + 'params must be a dictionary', fatal_error= True,exit_now=True)

    if type(default_params) != dict:
        msg_logger.msg('merge_with_defaults, parameter ' + crumbs + 'default_params must be a dictionary,  got type' + str(type(default_params)), fatal_error= True,exit_now=True)
    pass
    # first check if any keys in base or case params are not in defaults
    if check_for_unknown_keys:
        for key in list(params.keys()):
           if  key not in default_params :
                # get possible values without obsolete params
               possible_params=  [key for key, item in default_params.items() if not isinstance(item,_CheckerBaseClass) or  item.obsolete is None]
               msg_logger.spell_check('Parameter not recognised.',key,possible_params,caller=caller,
                           crumbs= crumbs + crumb_seperator + f'"{key}"', fatal_error=True)
    # add crumbs
    for key, item in default_params.items():
        parent_crumb = crumbs + crumb_seperator + key

        if key not in params: params[key] = None  # add default key to params if not present

        if type(item) in [ParamValueChecker, ParameterCoordsChecker]:
            params[key] = CheckParameterValues(key, item, params[key], parent_crumb, msg_logger, caller= caller)


        elif type(item) in [ParameterTimeChecker, ParameterValueChecker2]:
            params[key] = item.check_value(params[key],msg_logger, parent_crumb,  caller)

        elif type(item) == ParameterListChecker:
            params[key] = item.check_list(key,params[key],  msg_logger, parent_crumb)

            # process list of param dicts and merge with default param dict
            if item.acceptable_types == dict:
                dd = {} if item.default_value is None else item.default_value
                for n in range(len(params[key])):
                    params[key][n]= merge_params_with_defaults(params[key][n], dd, msg_logger, crumbs=parent_crumb + crumb_seperator + key + '[#' + str(n) + ']')

        elif type(item) == dict:
            # nested param dict
            #todo remove thsi option in fafoour of ParamValueDict of ParamClassDict

            # for some reason omiting base case keyword does not mean recursive call gets default, gets other unknown value??
              params[key] = merge_params_with_defaults(params[key], item,   msg_logger, crumbs=parent_crumb + crumb_seperator + key)

        else:
            msg_logger.msg('merge_params_with_defaults items in default dictionary can be ParamDictValueChecker, ParameterListChecker, or a nested param dict, ',
                           crumbs= parent_crumb,fatal_error = True)

    return params

def  CheckParameterValues(key,value_checker, user_param, crumbs, msg_logger,caller=None):
    # get value from ParamDictValueChecker
    if crumbs is None: crumbs = ''
    crumb_trail =f'{crumbs} {crumb_seperator} {key} '
    if user_param is None:
        if value_checker.is_required:
            msg_logger.msg('Required parameter: user parameter "' + crumb_trail +'" is required, must be type '
                           + str(value_checker.required_type) + ', Variable description:' + str(value_checker.doc_str),
                           fatal_error = True, caller=caller)
            value = None
        else:
            value = value_checker.get_default()
    else:
        # check the user given
        try:
            value = value_checker.check_value(user_param, msg_logger,crumbs=crumb_trail,caller=caller)
        except Exception as e:
            msg_logger.msg('unexpected error',key,crumbs)
            raise(e)


    return value
class _CheckerBaseClass(object): # duumy base to check if instance of this type
    def get_method_args_as_dict(self,m,locals):
        # get all args and values but self from method
        d={}
        for key in getfullargspec(m).args[1:]:
            d[key] = locals[key]
            setattr(self,key,locals[key])
        return d

class ParamValueChecker(_CheckerBaseClass):
    #todo change dtype to a list of possible types, and if not a list make a list

    def __init__(self, default_value, required_type, is_required=False,
                 min=None, max=None, units=None, possible_values=None,
                 doc_str=None,
                 obsolete = None,expert = False):

        # todo add crumb trail param

        if default_value is not None and type(default_value) == dict:
            raise ValueError('"value" of default set by ParamValueChecker (PVC) can not be a dictionary, as all dict in default_params are assumed to also be parameter dict in their own right')

        self.info = self.get_method_args_as_dict(self.__init__, locals())

        if self.required_type == bool: self.possible_values = [True, False]  # set possible values for boolean


    def get_default(self):
        return self.default_value


    def check_value(self,value, msg_logger, crumbs='', caller = None):
        # check given value against defaults  in class instance info
        crumbs = crumbs + ' > checking value against default'
        if value is not None and self.obsolete is not None:
            msg_logger.msg(f'Parameter is obsolete- "{self.obsolete}"',
                           fatal_error=True,crumbs= crumbs, caller= caller)
            return  None

        if value is None:
            # check default exits
            if self.is_required:
                msg_logger.msg('Required parameter: user parameter is required ',
                                crumbs = crumbs,caller= caller,
                               hint= ', must be type' + str(self.required_type) + ', Variable description:' + str(self.doc_str),fatal_error=True)

            value = self.default_value  # this might be a None default

        elif self.required_type == str:
            if type(value) in [np.str_]:
                value = str(value)
            elif type(value) != str:
                msg_logger.msg('Value must be a string, value is  "' + str(value) + '"', caller= caller,
                               fatal_error=True, crumbs = crumbs)

        elif self.required_type == float and type(value) == int:
            # ensure  ints are floats
            value = float(value)


        # deal with numpy versions of params, convert to python types
        elif self.required_type == int:
            # ensure all at int32 as default int is int64 on  linux
            value = np.int32(value)

        elif self.required_type == 'iso8601date':
            try:
                #test if convertable
                if type(value) == str:
                    value = time_util.isostr_to_seconds(value) # leave as a string
                elif type(value) == float or type(value) == np.float64:
                    # seconds since 1970
                    value = value
                else:
                    msg_logger.msg('Value must be iso8601 date string or seconds since 1/1/1970 as  a float got value = ' + str(value) + 'type='+ str(type(value)), caller=caller,
                                   fatal_error=True, crumbs=crumbs)
            except Exception as e:
                msg_logger.msg( 'Failed to convert to date as iso8601str got value = ' + str(value),caller= caller,
                                fatal_error=True, crumbs = crumbs)

        # if not one of special types above then value unchanged
        # check  value and type if not a None
        if value is not None:
            if type(self.required_type) != str and not type(value) != self.required_type and not isinstance(value, self.required_type):
                msg_logger.msg( 'Parameter data must be of type ' + str(self.required_type) + ' got type= ' + str(type(value)) + ' , value given =' +str(value),
                                caller= caller,  fatal_error=True, crumbs = crumbs)

            if (type(value) in [float, int]):

                if self.min is not None and value < self.min:
                    msg_logger.msg( 'Parameter must be >=' + str(self.min) + ', value given =  ' + str(value),caller= caller,
                                    fatal_error=True, crumbs = crumbs)

                if self.min is not None and self.max is not None and value > self.max:
                    msg_logger.msg('Parameter must be <= ' + str(self.min) + ', value given=  ' + str(value),caller= caller,
                                   fatal_error=True,  crumbs = crumbs)

            if self.possible_values is not None and len(self.possible_values) > 0 and value not in self.possible_values:
                msg_logger.msg('Parameter must be one of ' + str(self.possible_values) + ', value given =  ' + str(value),caller= caller,
                               fatal_error=True,  crumbs = crumbs)

        return value  # value may be None if default or given value is None

class ParameterListChecker(_CheckerBaseClass):
    # checks parameter list values
    # if default_list is None then list wil be None if user_list is not given
    # todo do should default value be a PVC() instance, to get control over  possible values in list , max, min etc?
    #todo do add option to allow appending to default only if requested
    def __init__(self, default_list, acceptable_types, is_required=False, can_be_empty_list= True, default_value=None,
                  fixed_len =None, min_length=None, max_length=None, doc_str=None, make_list_unique=None, obsolete = None,
                 possible_values=None, units=None,min=None, max=None,    expert = False
                 ):

        if default_list is None: default_list =[]

        self.info = self.get_method_args_as_dict(self.__init__,locals())

    def check_list(self, name, user_list, msg_logger, crumbs):

        if crumbs is None: crumbs = ''
        crumb_trail = crumbs + crumb_seperator + name

        if self.obsolete is not None and user_list is not None and len(user_list) > 0:
            msg_logger.msg(f'List Parameter is obsolete  - "{self.obsolete}"', fatal_error=True,
                           crumbs=crumb_trail)
            return None

        if user_list is not None and type(user_list) != list:
            msg_logger.msg(f'ParameterListChecker: must be a list, not type={str(type(user_list))} ',
                           fatal_error=True,crumbs=crumb_trail)

        if self.is_required and user_list is None:
            msg_logger.msg('ParameterListChecker: is a required parameter ',
                           fatal_error=True, crumbs=crumb_trail)
            
        # check default_value type
        if self.default_list is not None:
            for v in self.default_list:
                if v is not None and type(v) not in self.acceptable_types:
                    msg_logger.msg('ParameterListChecker: default list, type of item  ' + str(v) + ', must match list_type ' ,
                                   crumbs= crumb_trail,
                                   hint = 'acceptable types within are list= '+ str(self.acceptable_types), fatal_error=True)

        # merge lists, user, base and default lists
        # two types of list merge, appendable or required max size
        ul = [] if user_list is None else deepcopy(user_list)
        dl = [] if self.default_list is None else deepcopy(self.default_list)

         # check if user and base param are lists
        if type(ul) != list:
            msg_logger.msg('ParameterListChecker: both base and case parameters must be a lists ',
                           fatal_error=True,crumbs= crumb_trail)

        if self.fixed_len is None:
            complete_list = dl  + ul
            if self.make_list_unique is not None and self.make_list_unique:
                complete_list = list(set(complete_list)) # only keep unique list

        elif self.fixed_len is not None:
            complete_list = self.fixed_len*[None]
            complete_list[:len(dl)] = dl
            complete_list[:len(ul)] = ul # overwrite with user/case_lit param
            if complete_list == self.fixed_len*[None]: complete_list=[] # make empty if nothing set

        # check each of the list items
        for item in complete_list:

            if item is not None and type(item) not in self.acceptable_types:
                msg_logger.msg('ParameterListChecker: list must all be type ' + str(self.acceptable_types),
                               crumbs= crumb_trail,fatal_error=True)
            if self.min is not None and type(item) in [float, int] :
                if item < self.min:
                    msg_logger.msg(f'ParameterListChecker: given value {item}  must be >=  {self.min}',
                                   fatal_error=True, crumbs=crumb_trail)
            if self.max is not None and type(item) in [float, int]:
                if item > self.max:
                    msg_logger.msg(f'ParameterListChecker: given value {item}  must be <=  {self.max}', fatal_error=True,
                                   crumbs=crumb_trail)

        if len(complete_list) ==0 and  not self.can_be_empty_list:
            msg_logger.msg('ParameterListChecker: list must must not be empty and of types' + str(self.acceptable_types),
                           fatal_error=True,crumbs= crumb_trail)

        # check is all in acceptable values
        if self.possible_values is not None:
            for val in complete_list:
                if val not in self.possible_values:
                    pass
                    #todo add possible values checks

        return complete_list


class ParameterCoordsChecker(_CheckerBaseClass):
    # checks input cords or array is a set of N by 2 or 3 values
    def __init__(self,default_value, dtype=np.float64, is3D=False, single_cord=False, doc_str=None,one_or_more_points=False,
                  is_required=False, units='meters or , degrees if long_lat codes detected', min = None, obsolete = None,
                 expert=False):

        self.info = self.get_method_args_as_dict(self.__init__, locals())

    def get_default(self):
        return self.default_value

    def check_value(self,  value, msg_logger, crumbs='', caller=None):
        # check given value against defaults  in class instance info
        if crumbs is None: crumbs = ''
        crumb_trail= crumbs + '> coordinate params checker'
        # a position, eg release location, needs to be a numpy array

        if self.obsolete is not None :
            msg_logger.msg(f'Coordinate parameter is obsolete  - "{self.obsolete}"', fatal_error=True,
                           crumbs=crumb_trail)
            return None

        if type(value) not in [list, np.ndarray]:
            msg_logger.msg(f' expected param of type list or numpy array got type {type(value)}',
                           fatal_error=True, caller=caller, crumbs=crumb_trail)
            return None

        # attempt array conversion
        try:
            value = np.asarray(value)
        except Exception as e:
            msg_logger.msg(f'Coordinates must be numpy array or a list convertible to a numpy array ',
                           hint = f'got values {str(value)}',
                           crumbs = crumb_trail, fatal_error=True)



        # now have an array
        if not np.issubdtype(value.dtype, np.integer) and not np.issubdtype(value.dtype, np.float):
            msg_logger.msg(f'Coordinates must only contain floats ot ints, got type "{str(value.dtype)}" ',
                           hint=f'got values {str(value)}',
                           crumbs=crumb_trail, fatal_error=True)
            return None

        # make int float
        value= value.astype(np.float64)

        if self.min is not None and  np.any(value < self.min):
            msg_logger.msg(f'Values must be greater than minimum value of "{str(self.min)}" ',
                           hint=f'got values {str(value)}',  crumbs=crumb_trail, fatal_error=True)
        # if one or more expected make 1 by n
        if self.one_or_more_points and value.ndim==1:
            value= value.reshape((1,-1))
            self.single_cord = False

        # now have double array, so check shape
        if self.single_cord:
            # only expecting 2 or 3 cord values
            if value.shape[0] <2 or  value.shape[0] > 3 :
                msg_logger.msg(f'expecting coordinates with only 2 or 3 values',
                               hint=f'got values {str(value)}', crumbs=crumb_trail, fatal_error=True)

            if not self.is3D and value.shape[0] == 3:
                msg_logger.msg(f'expecting coordinates as 2D pair of values',
                               hint=f'got values {str(value)}', crumbs=crumb_trail, fatal_error=True)
            return value

        # must be a vector of coords and expect an N by 2 or 3 array
        if value.ndim == 1:
                msg_logger.msg(f'expecting N by 2 or 3 array, eg. [[2.4,4.5],[6.2,7.8],[6.6,9.]]',
                        hint=f'got values {str(value)}', crumbs=crumb_trail, fatal_error=True)
                return None

        if value.shape[1] < 2 or value.shape[1] > 3:
            msg_logger.msg(f'Expected and  vector N by 2 or 3 list or numpy array of coordinate pairs or triples, eg [[ 34., 56.]], ',
                   crumbs=crumb_trail,
                   hint =f'got size "{str(value.shape)}"', fatal_error=True)
            return None

        return value




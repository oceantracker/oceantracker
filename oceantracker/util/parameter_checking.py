from copy import deepcopy, copy
import numpy as np
from oceantracker.util import time_util
from oceantracker.util.message_and_error_logging import append_message
from oceantracker.util.message_and_error_logging import GracefulExitError
crumb_seperator= ' >> '


def check_top_level_param_keys_and_structure(params, template, required_keys=[], required_alternatives=[], tag=None, msg_list=[]):
    # ensure top level parameter dict has all keys, and any required ones

    if type(params) != dict:
        append_message(msg_list, 'Params must be a dictionary', tag=tag, exception = GracefulExitError)

    # check for required keys
    for key in required_keys:
        if key not in params:append_message(msg_list, 'Required param key  "' + key + '" is missing', tag=tag, exception = GracefulExitError)

    # check for required alternatives eg. required_alternatives=[['base_case_params','case_list' ]]
    for l in required_alternatives:
        has_alternative=False
        for key in l:
            if key in params:has_alternative=True
        if not has_alternative: append_message(msg_list, 'Params  must contain at least one of keys ' + str(l) + ' ', tag=tag, exception = GracefulExitError)

    # make sure all template keys are present
    for key, item in template.items():
        if key not in params:
            if type(item) == dict: params[key] = {}
            if type(item) == list: params[key] = []
        elif  type(params[key]) != type(item):
            append_message(msg_list, 'Param key = "' + key + '" must be type ' + str(type(item)) + ' not type' + str(type(params[key])), exception = GracefulExitError, tag=tag)

    # key for unexpected keys
    for key in params.keys():
        if key not in template.keys():
            append_message(msg_list, 'Unexpected key = "' + key + '" in parameters', warning=True, tag=tag)
            append_message(msg_list, 'must be one of keys = ' + str(list(template.keys())), tabs=1)

    return params, msg_list

def  merge_params_with_defaults(params, default_params, base_case, crumbs='', msg_list=[],   tag=None, check_for_unknown_keys=True):
    # merge nested paramteres with defaults, returns a copy of params updated
    # if param key is in base case then use base case rather than value from ParamDictValueChecker.get_default()
    # default dict. items must be one of 3 types
    # 1)  ParamDictValueChecker class instance
    # 2)   ParamDictListChecker class instance
    # crumbs is a string giving crumb trail to this parameter, for messaging purposes

    # merge into a copy of params to leave original unchanged
    params = deepcopy(params)

    if params is None : params ={}
    if type(params) != dict : raise ValueError('merge_with_defaults, parameter ' + crumbs + 'params must be a dictionary')
    if type(default_params) != dict: raise ValueError('merge_with_defaults, parameter ' + crumbs + 'default_params must be a dictionary')
    
    new_msg =[]

    # first check if any keys in base or case params are not in defaults
    if check_for_unknown_keys:
        for key in list(base_case.keys())+list(params.keys()):
           if key not in default_params:
               append_message(new_msg,'unrecognised parameter:' + crumbs + crumb_seperator + key, warning=True, tag=tag)


    for key, item in default_params.items():
        parent_crumb = crumbs + crumb_seperator + key


        if key not in params: params[key] = None  # add default key to params if not present
        if key not in base_case: base_case[key] = None  # add default key to params if not present

        if type(item) == ParamDictValueChecker:
            params[key], new_msg = CheckParameterValues(key, item, params[key], base_case[key], crumbs, new_msg)

        elif type(item) == ParameterListChecker:
            params[key], new_msg = item.check_list(key,params[key], base_case[key], new_msg, crumbs)

            # process list of param dicts and merge with default param dict
            if item.info['list_type'] == dict:
                dd = {} if item.info['default_value'] is None else item.info['default_value']
                for n in range(len(params[key])):
                    params[key][n], new_msg = merge_params_with_defaults(params[key][n], dd, {}, msg_list=new_msg, crumbs=parent_crumb + crumb_seperator + key + '[#' + str(n) + ']')

        elif type(item) == dict:
            # nested param dict
            # for some reason ommiting base case keyword does not mean recursive call gets default, gets other unknown value??
            bc = base_case[key] if key in base_case and base_case[key] is not None else {}
            params[key], new_msg = merge_params_with_defaults(params[key], item, bc,  msg_list=new_msg, crumbs=parent_crumb + crumb_seperator + key)
            a=1
        else:
            append_message(new_msg,'merge_params_with_defaults items in default dictionary can be ParamDictValueChecker, ParameterListChecker, or a nested param dict, '
                           + parent_crumb, exception = GracefulExitError, tag=tag)
    msg_list= msg_list + new_msg
    return params, msg_list

def  CheckParameterValues(key,value_checker, user_param, base_param, crumbs, msg_list):
    # get value from ParamDictValueChecker

    crumb_trail = crumbs + crumb_seperator + key
    if user_param is None and base_param is None:
        if value_checker.info['is_required']:
            append_message(msg_list, 'Required parameter: user parameter "' + crumb_trail +'" is required, must be type '
                           + str(value_checker.info['type']) + ', Variable description:' + str(value_checker.info['doc_str']), exception = GracefulExitError)
            value = None
        else:
            value = value_checker.get_default()

    elif user_param is None:
        # use value from base or default dict.
        value = base_param
        value,msg_list = value_checker.check_value(crumb_trail, base_param, msg_list)
    else:
        # check the user given
        value, msg_list= value_checker.check_value(crumb_trail, user_param, msg_list)

    return value, msg_list

class ParamDictValueChecker(object):
    def __init__(self, value, dtype, is_required=False, list_contains_type=None,
                 min=None, max=None,
                 possible_values=None,
                 doc_str=None,
                 class_doc_feature=None):

        if value is not None and type(value) == dict:
            raise ValueError('"value" of default set by ParamValueChecker (PVC) can not be a dictionary, as all dict in default_params are assumed to also be parameter dict in their own right')

        i = dict(default_value=value,
                 doc_str=doc_str,
                 class_doc_feature=class_doc_feature,
                 type=dtype,
                 min=min,
                 max=max,
                 possible_values=possible_values,
                 is_required=is_required,
                 list_contains_type=list_contains_type)

        if dtype == bool: i['possible_values'] = [True, False]  # set possible values for boolean

        self.info = i

    def get_default(self):
        return self.info['default_value']

    def check_value(self, crumb_trail, value, msg_list):
        # check given value against defaults  in class instance info
        i = self.info

        if value is None:
            # check default exits
            if self.info['is_required']:
                append_message(msg_list,'Required parameter: user parameter "' + crumb_trail + '" is required, must be type '
                               + str(i['type']) + ', Variable description:' + str(self.info['doc_str']), )
            value = i['default_value']  # this might be a None default

        elif i['type'] == str:
            if type(value) in [np.str_]:
                value = str(value)
            elif type(value) != str:
                append_message(msg_list,'Value for  "' + crumb_trail + '" must be a string, value is  "' + str(value) + '"', exception = GracefulExitError)

        elif i['type'] == float and type(value) == int:
            # ensure  ints are floats
            value = float(value)

        elif i['type'] == 'vector':
            # a position, eg release location, needs to be a numpy array
            m='Coordinate vector "' + crumb_trail + '" must be a list of coordinate pairs or triples, eg [[ 34., 56.]], convertible to N by 2 or 3 numpy array  '
            if type(value)  not in [list , np.ndarray]:
                append_message(msg_list,'Coordinate vector "' + crumb_trail + '", must be type list, or numpy array,  got type =' + str(type(value)) + ' , value given =' +str(value), exception = GracefulExitError)
            else:
                try:
                    value = np.asarray(value)
                    # now check shape
                    if value.ndim == 1 or  value.shape[1]  < 2 or  value.shape[1]  > 3:
                        append_message(msg_list, m, exception = GracefulExitError)

                except Exception as e:
                    append_message(msg_list, m, exception = GracefulExitError)

        # deal with numpy versions of params, convert to python types
        elif i['type'] == int and type(value) in [np.int8, np.int32, np.int16, np.int64]:
            value = int(value)

        elif i['type'] == 'iso8601date':
            try:
                time_util.date_from_iso8601str(value)
            except Exception as e:
                append_message(msg_list, 'Failed to convert to date as iso8601str "' + crumb_trail + '", value = ' + str(value), exception = GracefulExitError)

        # if not one of special types above then value unchanged
        # check  value and type if not a None
        if value is not None:

            if type(i['type']) != str and not type(value) != i['type'] and not isinstance(value, i['type']):
                append_message(msg_list, 'Parameter "' + crumb_trail + '" data must be of type ' + str(i['type']) + ' got type= ' + str(type(value)) + ' , value given =' +str(value), exception = GracefulExitError)
            if (type(value) in [float, int]):
                # print(name, value , i['min'])
                if i['min'] is not None and value < i['min']:
                    append_message(msg_list, 'Parameter "' + crumb_trail + '" must be >=' + str(i['min']) + ', value given =  ' + str(value), exception = GracefulExitError)

                if i['min'] is not None and i['max'] is not None and value > i['max']:
                    append_message(msg_list, 'Parameter "' + crumb_trail + '" must be <= ' + str(i['min']) + ', value given=  ' + str(value), exception = GracefulExitError)

            if i['possible_values'] is not None and len(i['possible_values']) > 0 and value not in i['possible_values']:
                append_message(msg_list, 'Parameter "' + crumb_trail + '" must be one of ' + str(i['possible_values']) + ', value given =  ' + str(value), exception = GracefulExitError)

        return value, msg_list  # value may be None if default or given value is None

class ParameterListChecker(object):
    # checks parameter list values
    # if default_list is None then list wil be None if user_list is not given
    # todo do should default value be a PVC() instance, to get control over  possible values in list , max, min etc?
    def __init__(self, default_list, list_type, is_required=False, can_be_empty_list= True, default_value=None,
                  fixed_len =None, min_length=None, doc_str=None, make_list_unique=None) :


        self.info= dict(locals()) # get keyword args as dict
        self.info.pop('self') # dont want self param

        requiredKW= ['default_list', 'list_type']
        for name in requiredKW:
            if name not in self.info:
                raise ValueError('ParameterListChecker > default_list, required key words ' + str(requiredKW))

    def check_list(self, name, user_list, base_list, msg_list, crumbs):
        i =self.info
        param_crumb_trail = crumbs + crumb_seperator + name

        if self.info['is_required'] and user_list is None and base_list is None:
            append_message(msg_list,'ParameterListChecker: param "' + param_crumb_trail + '" is required ', exception = GracefulExitError)
            
        # check default_value type
        for v in self.info['default_list']:
            if v is not None and type(v) not in i['list_type']:
                append_message(msg_list,'ParameterListChecker: param "' + param_crumb_trail + '" in default list, type of item  ' + str(v) + ', must match list_type ' + str(i['list_type']), exception = GracefulExitError)

        # merge non vector lists, user, base and default lists
        # two types of list merge, appendable or required max size
        ul = [] if user_list is None else deepcopy(user_list)
        bl = [] if base_list is None else deepcopy(base_list)
        dl = [] if i['default_list'] is None else deepcopy(i['default_list'])

        # check if user and base param are lists
        if type(bl) != list or type(ul) != list:
            append_message(msg_list,'ParameterListChecker: param "' + param_crumb_trail + '" both base and case parameters must be a lists ', exception = GracefulExitError)

        if i['fixed_len'] is None:
            complete_list = dl + bl + ul
            if i['make_list_unique'] is not None and i['make_list_unique']: complete_list = list(set(complete_list)) # only keep unique list

        elif i['fixed_len'] is not None:
            complete_list = i['fixed_len']*[None]
            complete_list[:len(dl)] = dl
            complete_list[:len(bl)] = bl  # over write with base list
            complete_list[:len(ul)] = ul # over write with user/case_lit param
            if complete_list == i['fixed_len']*[None]: complete_list=[] # make empty if nothing set

        # check each of the list items
        for item in complete_list:

            if item is not None and type(item) not in i['list_type']:
                append_message(msg_list,'ParameterListChecker: param "' + param_crumb_trail + '" list must all be type ' + str(i['list_type']), exception = GracefulExitError)

        if len(complete_list) ==0 and  not i['can_be_empty_list']:
            append_message(msg_list,'ParameterListChecker: param "' + param_crumb_trail + '" list must must not be empty ' + str(i['list_type']), exception = GracefulExitError)

        return complete_list,  msg_list




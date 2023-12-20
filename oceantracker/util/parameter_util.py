
from oceantracker import common_info_default_param_dict_templates as common_info
from oceantracker.util.module_importing_util  import import_module_from_string
from oceantracker.util.parameter_checking import merge_params_with_defaults

def make_class_instance_from_params(name, params,msg_logger, default_classID=None,
                                     crumbs='', merge_params=True,check_for_unknown_keys=True):
    # make a class instance  dynamically,  get instance of class from string eg oceantracker.solver.Solver
    # assumes class_name param exists
    # add class sequence number, used for in class list

    # work out class name
    if 'class_name' not in params or params['class_name'] is None:
        if default_classID is not None and  default_classID in common_info.default_classes_dict:
            params['class_name'] = common_info.default_classes_dict[default_classID]

        else:
            msg_logger.msg('params for ' + crumbs + ' must contain class_name, known default classes are ' + str(default_classID),
                            fatal_error=True, hint= 'given params are = ' + str(params), exit_now=True)

    i = import_module_from_string(params['class_name'], msg_logger,crumbs = crumbs + ' > importing module')
    i.info['name'] = name
    i.info['class_role'] = default_classID

    if merge_params:
        i.params  = merge_params_with_defaults(params, i.default_params, msg_logger, crumbs=crumbs,check_for_unknown_keys=check_for_unknown_keys)

    # attach the current message loger
    i.msg_logger = msg_logger
    return i
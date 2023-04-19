
from oceantracker.common_info_default_param_dict_templates import default_class_names, default_case_param_template
from oceantracker.util.module_importing_util  import import_module_from_string
from oceantracker.util.parameter_checking import merge_params_with_defaults

def make_class_instance_from_params(params,msg_logger, class_type_name=None, base_case_params =None,
                                    nseq=None, crumbs='', merge_params=True):
    # make a class instance  dynamically,  get instance of class from string eg oceantracker.solver.Solver
    if base_case_params is None : base_case_params={}

    # add class sequence number, used for in class list
    if nseq is None:
        nseq= 0
        sequ_tag = ''
    else:
        sequ_tag = '[#' + str(nseq) + '] '
    crumbs +=  sequ_tag

    # work out class name
    if 'class_name' not in params:  params['class_name'] = None

    if params['class_name'] is None and class_type_name is not None:
        # get from base case or default classes
        if 'class_name' in base_case_params and base_case_params['class_name'] is not None:
            params['class_name'] = base_case_params['class_name']
        elif class_type_name in default_class_names:
            params['class_name'] = default_class_names[class_type_name]
        else:
            msg_logger.msg('params for ' + crumbs + ' must contain class_name ' + class_type_name,
                           fatal_error=True, exit_now=True, hint= 'given params are = ' + str(params))

    #elif package_info is not None:
    #    # try to convert to long name
    #    if params['class_name'] in package_info['short_class_name_map']:
    #        params['class_name'] = package_info['short_class_name_map'][params['class_name']]

    i = import_module_from_string(params['class_name'],msg_logger)


    i.info['nseq']= nseq
    i.info['class_type'] = class_type_name

    if merge_params:
        # merge template with base case first
        if class_type_name in default_case_param_template and type(default_case_param_template[class_type_name]) != list:
            base_case_params = merge_params_with_defaults(base_case_params,
                                                    default_case_param_template[class_type_name], {},msg_logger,
                                                    check_for_unknown_keys=False,
                                                    crumbs=crumbs+'merging core clasess base case with case template' )

        i.params  = merge_params_with_defaults(params, i.default_params, base_case_params, msg_logger, crumbs=crumbs)

    # attach the current message loger
    i.msg_logger = msg_logger
    return i
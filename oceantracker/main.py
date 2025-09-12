from copy import  copy, deepcopy


from oceantracker import definitions
from oceantracker.util.message_logger import OTerror, MessageLogger
from oceantracker.oceantracker_params_runner import OceanTrackerParamsRunner
from  oceantracker.shared_info import shared_info

# use separate message logger for actions in main
msg_logger = MessageLogger()

OTname = definitions.package_fancy_name
help_url_base = 'https://oceantracker.github.io/oceantracker/_build/html/info/'

def run(params):
    '''Run a single OceanTracker case using given parameters'''

    ot = OceanTrackerParamsRunner()
    case_info_files = ot.run(deepcopy(params))  # run on copy to preserve external state
    return case_info_files


class OceanTracker():
    def __init__(self,params=None):
        self.params= {}
        msg_logger.set_screen_tag('helper')
        msg_logger.hori_line()
        msg_logger.msg(f'Starting OceanTracker helper class,  version {definitions.version["oceantracker_version"]} ')
        self.has_run = False

    # helper methods
    def settings(self,case=None, **kwargs):
        # work out if to add to base params or case list params
        if case is not None:
            msg_logger.msg('Cases run as seperate parallel processes are no longer supported, computations are now parallelized within a single process using threads',
                   hint='Remove case argument and computations will automatically be run on parallel threads by default',
                   caller = self,
                   fatal_error=True)
        for key in kwargs:
            self.params[key]= kwargs[key]

    def add_class(self, class_role:str=None, class_name:str=None, name: str=None, case:int=None,  **kwargs):
        '''
        Add a class instance in given role to computational pipeline, or add settings to a core class
        :param class_role: The role to add or set eg 'release_group'
        :param class_name: Name of class to import, required in some cases. eg "oceantracker.release_groups.polygon_release import PolygonRelease" or short name "PolygonRelease"
        :param name: Name of this instance of added class, used in output and internally to refer to this instance, eg 'my_polygon release'
        :param case: Add this instance to this case ID (>=0) to be run in parallel.
        '''
        ml = msg_logger
        known_class_roles = shared_info.core_class_roles.possible_values() + shared_info.class_roles.possible_values()

        if case is not None:
            ml.msg('Cases run as seperate parallel processes are no longer supported, computations are now parallelized within a single process using threads',
                   hint='Remove case argument and computations will automatically be run on parallel threads by default',
                   caller = self,
                   fatal_error=True)

        if class_role is None:
            ml.msg('oceantracker.add_class, must give first parameter as class role, eg. "release_group"', error=True, caller =self)
            return

        if type(class_role) != str:
            ml.msg('oceantracker.add_class, class_role must be a string got ', error=True, caller=self,
                   hint='Given type =' + str(type(class_role)))
            return

        if class_role not in known_class_roles:
            ml.spell_check(f'oceantracker.add_class, class_role parameter is not recognised, value ="{class_role}"',
                           class_role,known_class_roles, hint=f'Possible_values {str(known_class_roles)}')
            return

        params = self.params

        #add class name and name if given
        if class_name is not None: kwargs['class_name'] = class_name
        if name is not None: kwargs['name'] = name

        # add new params to core or other roles
        if class_role in shared_info.core_class_roles.possible_values():
            if class_role not in params: params[class_role] = {}
            params[class_role].update(kwargs)
        else:
            #add to mulit component role list
            if class_role not in params: params[class_role] = []
            if type(params[class_role]) != list:
                ml.msg(f'oceantracker.add_class {class_role} must be a list of dictionaries, with optional name key',
                       error=True, caller=self,  hint='Given type =' + str(type(params[class_role])))

            params[class_role].append(kwargs) # add users params

        return

    def run(self):
        ot_runner= OceanTrackerParamsRunner()
        # todo print helper message here at end??
        msg_logger.exit_if_prior_errors('Found errors see above')

        case_info_file = ot_runner.run(self.params)

        self.has_run = True
        # todo flag use so params can be reset if needed if same OceanTracker instance used more than once
        return case_info_file



# method to run ocean tracker from parameters
# eg run(params)
import sys

#


# Dev notes
# line debug?? python3.6 -m pyinstrument --show-all plasticsTrackOnLine_Main.py
# python -m cProfile
# python -m vmprof  <program.py> <program parameters>
# python -m cProfile -s cumtime

# do first to ensure its right

from copy import  copy, deepcopy


from oceantracker.util import setup_util, class_importer_util, time_util
from oceantracker import definitions
from oceantracker.util import json_util ,yaml_util, get_versions_computer_info
from oceantracker.util.message_logger import GracefulError, MessageLogger

from oceantracker._oceantracker_main_runner import _OceanTrackerRunner

import traceback

from  oceantracker.shared_info import shared_info

# use separate message logger for actions in main, cases use si.msg_logger
msg_logger = MessageLogger()

OTname = definitions.package_fancy_name
help_url_base = 'https://oceantracker.github.io/oceantracker/_build/html/info/'

def run(params):
    '''Run a single OceanTracker case using given parameters'''
    ot = _OceanTrackerRunner()
    case_info_files = ot.run(deepcopy(params))  # run on copy to preserve external state
    return case_info_files


class OceanTracker():
    def __init__(self,params=None):
        self.params= {}
        msg_logger.set_screen_tag('helper')
        msg_logger.print_line()
        msg_logger.msg('Starting OceanTracker helper class')
        self.has_run = False

    # helper methods
    def settings(self,case=None, **kwargs):
        # work out if to add to base params or case list params
        existing_params = self._get_case_params_to_work_on(case)
        for key in kwargs:
            existing_params[key]= kwargs[key]

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

        if class_role is None:
            ml.msg('oceantracker.add_class, must give first parameter as class role, eg. "release_group"', error=True, caller =self)
            return

        if type(class_role) != str:
            ml.msg('oceantracker.add_class, class_role must be a string got ', error=True, caller=self,
                   hint='Given type =' + str(type(class_role)))
            return

        if class_role not in known_class_roles:
            ml.spell_check(f'oceantracker.add_class, class_role parameter is not recognised, value ="{class_role}"',
                           class_role,known_class_roles, error=True, hint=f'Possible_values {str(known_class_roles)}')
            return

        existing_params = self._get_case_params_to_work_on(case)

        #add class name and name if given
        if class_name is not None: kwargs['class_name'] = class_name
        if name is not None: kwargs['name'] = name

        # add new params to core or other roles
        if class_role in shared_info.core_class_roles.possible_values():
            if class_role not in existing_params: existing_params[class_role] = {}
            existing_params[class_role].update(kwargs)
        else:
            #add to mulit component role list
            if class_role not in existing_params: existing_params[class_role] = []
            if type(existing_params[class_role]) != list:
                ml.msg(f'oceantracker.add_class {class_role} must be a list of dictionaries, with optional name key',
                       error=True, caller=self,  hint='Given type =' + str(type(existing_params[class_role])))

            existing_params[class_role].append(kwargs) # add users params

        return

    def _get_case_params_to_work_on(self, case):
        # work out whether to work on base of given case
        if case is None:
            # base case only
            return self.params
        else:
            if 'case_list' not in self.params: self.params['case_list'] = []
            case_list = self.params['case_list']
            if type(case) != int or case < 0:
                msg_logger.msg(f'Case keyword must be an integer >=0', error=True, hint=f'Got value :{str(case)}')

            if case < len(case_list):
                return case_list[case] # work on existing case
            elif case == len(case_list):
                # next in line case
                case_list.append({}) # expand by  one extra cases as empty
                return case_list[case] # work on new last one
            else:
                msg_logger.msg(f'New cases must be added in order, have case = {case}',error=True,
                     hint=f"This would be the {case + 1}'th case added, but only :{len(case_list)} cases have been added so far" )
                return {}

    def run(self):
        msg_logger.progress_marker('Starting run using helper class')
        ot_runner= _OceanTrackerRunner()
        # todo print helper message here at end??
        msg_logger.exit_if_prior_errors('Found errors see above')

        case_info_file = ot_runner.run(self.params)

        self.has_run = True
        # todo flag use so params can be reset if needed if same OceanTracker instance used more than once
        return case_info_file



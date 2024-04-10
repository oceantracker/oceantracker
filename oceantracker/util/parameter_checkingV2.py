from dataclasses import  dataclass, field
import datetime
from typing import List
import numpy as np
from oceantracker.util import  time_util

@dataclass
class _ParameterBaseDataClassChecker():
    default: field(default=None, metadata={"required": True})
    possible_types: List = field(default_factory=lambda: [str, float])
    expert : bool= False
    obsolete: bool = False
    is_required: bool = False
    doc_str : str = None
    units: str = None

    def __post_init__(self):
        pass
    def get_default(self): return self.default

    def asdict(self): return self.__dict__

    def check_value(self, value, msg_logger, crumbs,  caller):
        if self.obsolete:
            msg_logger.msg(f'Parameter is obsolete- "{self.obsolete}"',
                           fatal_error=True,crumbs= crumbs, caller= caller)

        if value is None and self.is_required:
            # check if required
            msg_logger.msg('Required parameter: user parameter is required ', crumbs = crumbs,caller= caller,
                               hint= ', must be type' + str(self.possible_types) + ', Variable description:' + str(self.doc_str),fatal_error=True)
        return value

@dataclass
class ParameterTimeChecker(_ParameterBaseDataClassChecker):
    possible_types: List =  field(default_factory=lambda: [str, float, int])
    units: str = 'ISO 8601  date as string eg. "2017-01-01T00:30:00, or float of seconds since 1/1/1970'
    def check_value(self, value, msg_logger, crumbs,  caller):

        crumbs = 'ParameterTimeChecker > ' + crumbs
        value = super().check_value(value, msg_logger, crumbs, caller)

        try:
            match value:
                case str():
                    value = time_util.isostr_to_seconds(value) # convert iso string

                case int() | float() | np.float64() | np.float32():
                    # seconds since 1970
                    value = float(value)
                case datetime.datetime():
                    value = datetime.utcfromtimestamp(value)

        except Exception as e:
                msg_logger.msg( f'Failed to convert to date got value = "{str(value)}", type = "{str(type(value))}"',caller= caller,
                                hint='Must be ISO string eg, 2017-01-01T03:30:00, or int, or a float as seconds since 1/1/1970',
                                fatal_error=True, crumbs = crumbs)
        pass

@dataclass
class ParameterValueChecker2(_ParameterBaseDataClassChecker):

    type : any = None
    min: float = None
    max: float = None
    possible_values : List = field(default_factory=lambda: [])


    def __post_init__(self):
        super().__post_init__()

        # add information for booleans
        if type(self.default) == bool:
            self.possible_values = [True, False]
            self.type = [bool]

        # define possible types
        self.possible_types += [self.type]
        if self.type == float:
            self.possible_types += [int, np.float64, np.float32]

        if type(self.possible_values) != list: self.possible_values = [self.possible_values]



    def check_value(self, value, msg_logger, crumbs,  caller):
        crumbs = 'ParameterValueChecker > ' + crumbs
        value = super().check_value( value, msg_logger, crumbs,  caller)

        # just return default, which may be a None
        if value is None:
            return self.default

        if value not in self.possible_values:
            msg_logger.msg('Parameter must be one of ' + str(self.possible_values) + ', value given =  ' + str(value), caller=caller,
                           fatal_error=True, crumbs=crumbs)
            return None

        if self.type == bool: return value

        if self.type == float: return float(value)


        pass
# old versions
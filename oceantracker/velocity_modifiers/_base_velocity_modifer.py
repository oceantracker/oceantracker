# is a base fro two types of classes which change either
# 1) the interpolated hindcast velocity,( eg add particle terminal velocity, stokes drift etc)
# 2) the terajectory of the particle eg, resuspension

from oceantracker.util import basic_util
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC
from oceantracker.util.parameter_base_class import ParameterBaseClass

class VelocityModiferBase(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC(None,str),'is3D': PVC(False,bool)})

    def initialize(self):pass


    # prototype for velocity modification of v, at some space and time for isActive particles
    def modify_velocity(self, v, time, active): basic_util.nopass('velocity modify must have a  modify_velocity method ')
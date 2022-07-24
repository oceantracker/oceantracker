# is a base fro two types of classes which change either
# 1) the interpolated hindcast velocity,( eg add particle terminal velocity, stokes drift etc)
# 2) the terajectory of the particle eg, resuspension

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamDictValueChecker as PVC

class _BaseTrajectoryModifer(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'name': PVC(None,str),'is3D': PVC(False,bool)})

    def initialize(self,**kwargs): pass

        # set up shortcut to dat requied to modify velocity  below      eg.
        #self.x_data= self.aunt('particle_group_manager').property_data_ptr('x')

    # prototype for status modification,
    #  all particles tested to see if they need status changing, eg tidal stranding
    def update(self, nb, time, active): pass

# is a base fro two types of classes which change either
# 1) the interpolated hindcast velocity,( eg add particle terminal velocity, stokes drift etc)
# 2) the terajectory of the particle eg, resuspension

from oceantracker.util.parameter_base_class import ParameterBaseClass
from oceantracker.util.parameter_checking import ParamValueChecker as PVC

class _BaseTrajectoryModifer(ParameterBaseClass):

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params({'is3D': PVC(False,bool)})

    def initial_setup(self, **kwargs): pass

        # set up shortcut to dat requied to modify velocity  below      eg.
        #self.x_data= self.aunt('particle_group_manager').property_data_ptr('x')

    # prototype for status modification,
    #  all particles tested to see if they need status changing, eg tidal stranding
    def update(self, n_time_step, time_sec, active): pass




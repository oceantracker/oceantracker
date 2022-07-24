from oceantracker.util.parameter_base_class import ParameterBaseClass
import oceantracker.util.basic_util  as basic_util

class _BaseInterp(ParameterBaseClass):
    # prototype for interplotor

    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.grid={'x':None, 'triangles':None, 'adjacency': None,'land_nodes':None, 'open_nodes': None,'bc_transform': None }

    def initialize(self,**kwargs): pass

    def build_grid(self): basic_util.nopass(' must supply find_build_grid')

    # find hori and vertical cell containing each particle
    def find_cell(self, xq, nb, active): basic_util.nopass(' must supply find_cells method')

    def get_depth_cell(self, xq, nb, step_dt_fraction, active):basic_util.nopass(' must supply get_depth_cell method')  # used by find_cell in 3D

    def eval_interp2D_timeIndependent(self, xq, nb, active):    basic_util.nopass(' must supply eval_interp2D_timeIndependent method')
    def eval_interp3D_timeIndependent(self, xq, nb, active):    basic_util.nopass(' must supply interp3D_timeIndependent method')
    def eval_interp2D_timeDependent(self, xq, nb, active):      basic_util.nopass(' must supply eval_interp2D_timeDependent method')
    def eval_interp3D_timeDependent(self, xq, nb, active):      basic_util.nopass(' must supply eval_interp3D_timeDependent method')

    # return cell number for xq without a guess
    def initial_cell_guess(self, xq, active): pass

    def close(self): pass




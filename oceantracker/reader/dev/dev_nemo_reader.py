from oceantracker.reader.generic_stuctured_reader import dev_GenericStructuredReader
from oceantracker.util.parameter_checking import ParamValueChecker as PVC, ParameterListChecker as PLC
from oceantracker.util.ncdf_util import NetCDFhandler

class NemoReader(dev_GenericStructuredReader):
    # reads  ROMS file, and tranforms all data to PSI grid
    # then splits all triangles in two to  use in oceantracker as a triangular grid,
    # so works with curvilinear ROMS grids
     # note: # ROMS is Fortan code so np.flatten() in F order

    def __init__(self):
        #  update parent defaults with above
        super().__init__()  # required in children to get parent defaults

        # test reading to view file
        fn=r'E:\H_Local_drive\ParticleTracking\hindcast_formats_examples\nemo\ORCA025-N06_20000104d05U.nc'
        nc = NetCDFhandler(fn)
        pass

from oceantracker.util.ncdf_util import NetCDFhandler
import numpy as np
from time import perf_counter



if __name__ == "__main__":

    fn= 'G:\\Hindcasts_large\\MalbroughSounds_10year_benPhD\\2008\\schism_marl20080101_00z_3D.nc'
    nc= NetCDFhandler(fn,'r')
    var = 'hvel'
    for nb in range(1,25):

        data= np.full( (nb,) + nc.get_var_shape(var)[1:],0.,nc.get_var_dtype(var))

        t0 = perf_counter()
        data[:nb,...] = nc.read_a_variable(var,sel=np.arange(nb))
        #data[:nb, ...] = nc.file_handle[var][:nb,...]
        print((perf_counter()-t0)/nb)

    nc.close()




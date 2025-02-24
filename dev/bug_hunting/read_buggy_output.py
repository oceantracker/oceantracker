import numpy as np

from read_oceantracker.python import load_output_files
from read_oceantracker.python import read_ncdf_output_files
from matplotlib import pyplot as plt
from os import path
from plot_oceantracker.plot_statistics import animate_heat_map

output_dir = r'\\CCL-AKL-STORE01.cawthron.org.nz\Malcolm$\OTDebug20250224\oceantracker_penConfig1z\faecesNR'
case_info_file = path.join(output_dir, 'faecesNR_caseInfo.json')

#d = load_output_files.load_stats_data(case_info_file)
stats_file = path.join(output_dir, 'faecesNR_stats_gridded_time_2D_0_heatMap_North.nc')
d0 = read_ncdf_output_files.read_stats_file(stats_file)

pass
t = (d0['time']-d0['time'][0])/3600/24.
plt.plot(t,d0['count_all_particles'])
plt.show()

plt.plot(t,np.squeeze(d0['count'][:, 0,:,:].sum(axis=2)))

plt.show()

animate_heat_map(case_info_file,release_group=0)



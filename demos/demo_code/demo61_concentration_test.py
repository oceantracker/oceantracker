# demo61_concentration_test.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("..\demo_param_files\demo61_concentration_test.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo61_concentration_test

# below only required for plotting
from oceantracker.post_processing.read_output_files.load_output_files import load_concentration_data, get_case_info_file_from_run_file
from oceantracker.post_processing.plotting.plot_statistics import animate_concentrations

output_file= "output\demo61_concentration_test"

c = load_concentration_data(case_info_file_name, var_list=['particle_concentration', 'C'])

axis_lims = [1591000, 1601500, 5478500, 5491000]

animate_concentrations(c, data_to_plot=c['particle_concentration'], logscale=True,
                                    axis_lims=axis_lims, cmap='hot_r',
                                    heading='SCHISIM-3D, 2D concentrations in triangles, shading',
                                    movie_file=output_file + '_shading.mp4' if output_file is not None else None,
                                    fps=7, interval=20,
                                    vmin =0., vmax=1.0)
animate_concentrations(c, data_to_plot=c['particle_count'],logscale=True,
                                    axis_lims=axis_lims, cmap='hot_r', shading=False, interval=200,
                                    heading='SCHISIM-3D, 2D particle counts in triangles, noshading',
                                    fps=7,
                                    movie_file=output_file + '_noshading.mp4' if output_file is not None else None,
                                    )

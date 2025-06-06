# demo56_SCHISM_3D_resupend_crtitical_friction_vel.py
#---------------------------------------
import oceantracker.main as main
from oceantracker.util import json_util
params = json_util.read_JSON("../demo_param_files/demo56_SCHISM_3D_resupend_crtitical_friction_vel.json")

runInfo_file_name, has_errors = main.run(params)

# output is now in output/demo56_SCHISM_3D_resupend_crtitical_friction_vel

# below only required for plotting
from oceantracker.read_output.python import load_track_data
from oceantracker.plot_output.plot_tracks import animate_particles

output_file= "output\demo56_SCHISM_3D_resupend_crtitical_friction_vel"

track_data = load_track_data(case_info_file_name, fraction_to_read=.9)
ax_lims= [1591000, 1601500, 5478500, 5491000]
animate_particles(track_data, axis_lims=ax_lims,
                  heading='SCHISIM 3D, fall velocity and critical friction velocity resuspension',
                  movie_file=output_file + '_status.mp4' if output_file is not None else None,
                  fps=15, show_dry_cells=True, interval=20)

animate_particles(track_data, axis_lims=ax_lims,
                            colour_using_data=track_data['z'],
                            part_color_map='winter_r',
                            vmin=-20,
                            vmax=0,
                            heading='SCHISIM 3D, fall velocity and crtitical friction velocity resuspension, particles coloured by depth',
                            movie_file=output_file + '_depth.mp4' if output_file is not None else None,
                            fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)

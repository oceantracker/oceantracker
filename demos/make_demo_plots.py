

def demo01_plot_tracks(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars
    from oceantracker.post_processing.plotting.plot_tracks import plot_tracks

    track_data = load_particle_track_vars(case_info_file_name)
    plot_tracks(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                 heading='Tracks, point release',
                 plot_file_name=output_file + '.jpeg' if output_file is not None else None)
    return None

def demo02_animation(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles

    track_data = load_particle_track_vars(case_info_file_name, fraction_to_read=0.9)

    animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],show_grid=True,
                                heading='3 hourly point and polygon releases with tidal stranding',
                                release_group=None,
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)
    return None

def demo03_heatmaps(case_info_file_name, output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_stats_file
    from oceantracker.post_processing.plotting.plot_statistics import plot_heat_map, animate_heat_map


    stats_data = load_stats_file(case_info_file_name)
    axis_lims = [1591000, 1601500, 5478500, 5491000]
    animate_heat_map(stats_data,'myP1', axis_lims=axis_lims,
                                    heading='Particle count heatmaps built on the fly, no tracks recorded, log scale',
                                    movie_file=output_file + '.mp4' if output_file is not None else None,
                                    fps=7)
    plot_heat_map(stats_data,'myP1', axis_lims=axis_lims, var='water_depth', heading='Water depth built on the fly, no tracks recorded',
                                 plot_file_name=output_file + '_water_depth.jpeg' if output_file is not None else None)
    return None

def demo04_ageBasedHeatmaps(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_stats_file, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_statistics import plot_heat_map, animate_heat_map



    stats_data = load_stats_file(case_info_file_name,name='age_grid')
    axis_lims = [1591000, 1601500, 5478500, 5491000]
    animate_heat_map(stats_data,'myP1', axis_lims=axis_lims,
                                    heading='Particle count heatmaps built on the fly, no tracks recorded, log scale',
                                    movie_file=output_file + '.mp4' if output_file is not None else None,
                                    fps=7)
    return None

def demo05_parallel(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_stats_file, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_statistics import plot_heat_map, animate_heat_map
    # parallel run no plot
    return None


def demo06_reefstranding(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles

    track_data = load_particle_track_vars(case_info_file_name)

    animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                                heading='Trajectory Modifer example, particles liking a reef',
                                release_group=None,
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15, back_ground_depth=True, show_dry_cells=True, interval=50)
    return None


def demo07_inside_polygon_events(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file, read_case_info_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles
    from matplotlib import colors

    caseInfo = read_case_info_file(case_info_file_name)
    track_data = load_particle_track_vars(case_info_file_name, var_list=['event_polygon'])

    cmap = colors.ListedColormap(['b', 'm', 'y'])
    animate_particles(track_data, colour_using_data=track_data['event_polygon'],
                                    part_color_map=cmap,
                                    axis_lims=[1591000, 1601500, 5478500, 5491000],
                                    heading='Event logger, polygon aware particles',
                                    vmin=-1,
                                    vmax=1,
                                    movie_file=output_file + '.mp4' if output_file is not None else None,
                                    fps=15,
                                    polygon_list_to_plot=caseInfo['full_case_params']['role_dicts']['event_loggers']['in_out_poly']['polygon_list'],
                                    show_dry_cells=True, interval=30)
    return None


def demo08_particle_splitting(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles



    track_data = load_particle_track_vars(case_info_file_name)

    animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                                heading='Split moving particles in two and culling 5%  every 6 hours',
                                min_status=-2,
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)
    return None

def demo09_polygon_release_overlapping_land(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles


    track_data = load_particle_track_vars(case_info_file_name)

    animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                                heading='Polygon release 1) overlaping land, and 2) min 30m,  water depth',
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                show_grid=False,
                                fps=15, back_ground_depth=True, show_dry_cells=True, interval=50)
    return None

def demo10_polygon_residence_demo(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file,load_residence_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles
    from oceantracker.post_processing.plotting.plot_statistics import plot_residence

    residence_data = load_residence_file(case_info_file_name)
    plot_residence(residence_data, heading='Number residence in release polygon demo',
                   plot_file_name=output_file + '.jpeg' if output_file is not None else None)

    track_data = load_particle_track_vars(case_info_file_name, fraction_to_read=0.9)
    animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],show_grid=True,
                                heading='Residence in release polygon counts demo',
                                release_group=None,
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)

    return None

def demo50_SCHISM_depthAver(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles

    track_data = load_particle_track_vars(case_info_file_name)

    animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                                heading='Schsim',
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)
    return None

def demo55_SCHISM_3D_fall_velocity(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles

    track_data = load_particle_track_vars(case_info_file_name)

    animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000], show_grid=False,
                                heading='SCHISIM reader, 3D, fall velocity and bottom stranding',
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)
    return None

def demo56_SCHISM_3D_resupend_crtitical_friction_vel(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles

    track_data = load_particle_track_vars(case_info_file_name, fraction_to_read=.9)
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
    return None

def demo57_SCHISM_3D_lateralBoundaryTest(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles

    track_data = load_particle_track_vars(case_info_file_name)

    animate_particles(track_data, axis_lims=[1598000, 1601500, 5482000, 5488000],
                                heading='SCHISIM reader, lateral boundary test',
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)
    return None

def demo58_bottomBounce(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles
    from oceantracker.post_processing.plotting.plot_vertical_tracks import plot_path_in_vertical_section, plot_relative_height

    track_data = load_particle_track_vars(case_info_file_name, var_list=['tide', 'water_depth'])

    plot_path_in_vertical_section(track_data,  title= 'fall velocity and resuspension with critical friction velocity ',
                                          plot_file_name=output_file +  '_section.jpeg' if output_file is not None else None)

    plot_relative_height(track_data, title='fall velocity, always resuspension_jump ')
    plot_relative_height(track_data, title='fall velocity, always resuspension_jump ', bottom=False)

    animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000], heading='vertical section tracks')
    return None

def demo59_crit_shear_resupension(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_vertical_tracks import plot_path_in_vertical_section

    track_data = load_particle_track_vars(case_info_file_name, var_list=['tide', 'water_depth'])

    plot_path_in_vertical_section(track_data, title='Fall velocity, critical friction velocity  resuspension ',
                                                       plot_file_name=output_file +  '_section.jpeg' if output_file is not None else None)
    return None


def demo60_SCHISM_3D_decaying_particle(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles

    track_data = load_particle_track_vars(case_info_file_name, var_list=['tide', 'water_depth', 'age_decay'])

    animate_particles(track_data, axis_lims=[1591000, 1601500, 5478500, 5491000],
                                heading='SCHISIM reader, 3D, decaying particles, decay time 3.5 hrs',
                                colour_using_data=track_data['age_decay'], part_color_map='hot_r',
                                size_using_data=track_data['age_decay'],
                                vmax=1.0,
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=24,
                                interval=20, show_dry_cells=True)
    return None

def demo61_concentration_test(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_concentration_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_statistics import animate_concentrations

    c = load_concentration_vars(case_info_file_name, var_list=['particle_concentration', 'C'])

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
    return None


def demo70_ROMS_reader(case_info_file_name,output_file=None):
    from oceantracker.post_processing.read_output_files.load_output_files import load_particle_track_vars, get_case_info_file_from_run_file
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles

    track_data = load_particle_track_vars(case_info_file_name, fraction_to_read=0.9)

    animate_particles(track_data, axis_lims=None,show_grid=True,
                                heading='ROMs reader test',
                                release_group=None,
                                movie_file=output_file + '.mp4' if output_file is not None else None,
                                fps=15, back_ground_depth=True, show_dry_cells=True, interval=20)
    return None

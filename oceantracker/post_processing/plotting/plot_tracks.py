import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors, animation
from oceantracker.post_processing.plotting import plot_utilities

from oceantracker.post_processing.read_output_files import load_output_files
#from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

from oceantracker.util import time_util

def plot_tracks(track_data, show_grid=False,credit=None, heading =None,
                title=None, axis_lims=None, show_start=False, back_ground_depth=True, back_ground_color_map= None,
                plot_file_name=None, polygon_list_to_plot = None):

    fig = plt.gcf()
    ax = plt.gca()

    fig.tight_layout()

    plot_utilities.draw_base_map(track_data['grid'],ax=ax, axis_lims=axis_lims, show_grid= show_grid, title=title, credit=credit,
                  back_ground_depth=back_ground_depth,back_ground_color_map= back_ground_color_map)

    ax.plot(track_data['x'][:,:, 0], track_data['x'][:, :, 1], linewidth=.5)
    if show_start:
        # show all starts, eg random within polygon
        ax.scatter( track_data['x0'][ :, 0],  track_data['x0'][ :, 1], edgecolors=None, c='green', s=4, zorder =8)

    plot_utilities.plot_release_points_and_polygons(track_data, ax=ax) # these are nominal starts
    plot_utilities.draw_polygon_list(polygon_list_to_plot,ax=ax)
    plot_utilities.show_particleNumbers(track_data['x'].shape[1])
    plot_utilities.add_heading(heading)
    plot_utilities.show_output(plot_file_name=plot_file_name)

def animate_particles(track_data, axis_lims=None, colour_using_data= None, show_grid=False, title=None, max_duration=None,
                      movie_file= None, fps=10, dpi=300, interval=50, size=8,
                      polygon_list_to_plot = None, min_status=0,
                      back_ground_depth=True, back_ground_color_map = None, credit=None, heading= None,
                      size_using_data= None,  part_color_map=None,
                      vmin=None, vmax=None, aspect_ratio=None,
                      release_group=None, show_dry_cells = False, show=True):
    def draw_frame(nt):
        if show_dry_cells:
            dry_cell_plot.set_array(dry_cell_data[nt, :])

        # only plot alive particles
        x = track_data['x'][nt, :, :2].copy() # copy so as not to change original data
        sel = track_data['status'][nt, :] < min_status # get rid of dead particles
        x[sel,:] = np.nan
        sc.set_offsets(x)
        sc.set_array(colour_using_data[nt, :].astype(np.float64))
        sc.set_zorder(5)
        # force release points on top
        for rp in release_pts:
            rp.set_zorder(9)

        if size_using_data is not None: sc.set_sizes(scaled_marker_size[nt, :])
        time_text.set_text(time_util.seconds_to_pretty_str(track_data['time'][nt], seconds=False))
        return  (sc,time_text, dry_cell_plot) + tuple(release_pts)

    if max_duration is  None:
        num_frames = track_data['time'].shape[0]
    else:
        num_frames = min(int( track_data['time'].shape[0]*max_duration /abs(track_data['time'][-1]-track_data['time'][0]) ),track_data['time'].shape[0])

    fig = plt.gcf()
    ax = plt.gca()
    if aspect_ratio is not None:
        ax.set_aspect(aspect_ratio)
        fig.set_size_inches(3, 6)
        plt.axis('scaled')

    plot_utilities.draw_base_map(track_data['grid'], ax=ax, axis_lims=axis_lims, show_grid=show_grid, title=title, credit=credit,
                  back_ground_depth=back_ground_depth, back_ground_color_map=back_ground_color_map)

    dry_cell_plot,dry_cell_data = plot_utilities.plot_dry_cells(track_data,show_dry_cells)


    s0 =size
    nt = num_frames-1
    if colour_using_data is not None:
        clims = [np.nanmin(colour_using_data), np.nanmax(colour_using_data)]
        cmap = part_color_map
        print('animate_particles: color map limits', vmin, vmax)
        sc = ax.scatter(track_data['x'][nt, :, 0], track_data['x'][nt, :, 1], s=s0, c=colour_using_data[nt, :], edgecolors=None,
                        vmin=clims[0] if vmin is None else vmin,
                        vmax=clims[1] if vmax is None else vmax, cmap=cmap, zorder=5)
    else:
        # colour by status
        colour_using_data = np.full_like(track_data['status'], -127)

        stat_types = track_data['particle_status_flags']
        status_list = [stat_types['outside_open_boundary'],stat_types['dead'],  stat_types['stationary'], stat_types['stranded_by_tide'], stat_types['on_bottom'], stat_types['moving']]
        for n, val in enumerate(status_list):
            colour_using_data[track_data['status']==val] = n # replace status with range(status_list)

        colour_using_data = colour_using_data.astype(np.float64)
        status_colour_map = np.asarray([[0.6,    0.2,    0.2],[0, 0., 0.],[.8, 0, 0.],  [0, .5, 0.], [0.5, 0.5, .5], [0, 0, 1.] ])
        cmap = colors.ListedColormap(status_colour_map)

        sc = ax.scatter(track_data['x'][nt, :, 0], track_data['x'][nt, :, 1], c=colour_using_data[nt, :], vmin=0,
                        vmax=len(status_list), s=s0, edgecolors=None, cmap=cmap, zorder=5)

    release_points_obj = plot_utilities.plot_release_points_and_polygons(track_data, ax=ax, release_group=release_group)
    release_pts= []
    for rp in release_points_obj:
        for rpi in rp:
           release_pts.append((rpi))
    release_pts=tuple(release_pts)

    plot_utilities.draw_polygon_list(polygon_list_to_plot, ax=ax)

    if size_using_data is not None:
        # linear sizing on field range
        slims = [np.nanmin(size_using_data), np.nanmax(size_using_data)]
        scaled_marker_size = s0 * (size_using_data-slims[0]) /(slims[1]-slims[0])

    time_text = plt.text(.05, .05, time_util.seconds_to_pretty_str(track_data['time'][0], seconds=False), transform=ax.transAxes)
    plot_utilities.add_heading(heading)
    plot_utilities.show_particleNumbers(track_data['x'].shape[1])
    fig.tight_layout()

    anim = animation.FuncAnimation(fig, draw_frame, frames=num_frames, interval=interval, blit=True)
    plot_utilities.animation_output(anim, movie_file, fps=fps, dpi=dpi, show=show)
    return anim



# plot a case
# most require dict returned by readOutputFiles.read_runCaseInfo as input,
import numpy as np
import matplotlib.pyplot as plt
from oceantracker.util.triangle_utilities import convert_face_to_nodal_values
import plot_oceantracker.plot_utilities as plot_utilities

from matplotlib import animation
from oceantracker.util import time_util

def animate_heat_map(stats_data, release_group, var='count',  axis_lims=None, credit=None, interval=20,heading=None,
                     vmin=None, vmax=None,show_grid=False,title=None,logscale=False, caxis= None,cmap='viridis',
                     movie_file= None, fps=15, dpi=300,  back_ground_depth=True, back_ground_color_map= None):

    def draw_frame(nt):

        x,y, z = _get_stats_data(nt, stats_data, var, release_group, logscale, zmin=caxis[0])
        pc.set_array(z.ravel())
        pc.set_clim(caxis[0],caxis[1])
        if 'time' in stats_data:
            time_text.set_text(time_util.seconds_to_pretty_str(stats_data[stats_data['time_var']][nt],seconds=False))
        else:
            # aged based
            time_text.set_text('Age bin: %02.1f days' % (stats_data[stats_data['time_var']][nt]/24/3600))

        return pc, time_text

    fig = plt.gcf()
    ax = plt.gca()
    zmin = np.nanmin(stats_data[var])
    zmax = np.nanmax(stats_data[var])

    x, y, z  = _get_stats_data(-1, stats_data, var, release_group, logscale, zmin=vmin)
    caxis = [zmin if vmin is None else vmin, zmax if vmax is None else vmax]

    if not back_ground_depth:
        z[np.isnan(z)]= vmin

    print('animate_heat_map> colour axis limits',[zmin,zmax], caxis)
    pc = ax.pcolormesh(x,y, z, shading='gouraud', zorder= 2, cmap=cmap, edgecolor='none')

    if axis_lims is None:    axis_lims=[x[0],x[-1],y[0],y[-1]] # set axis limits to those of the grid

    plot_utilities.draw_base_map(stats_data['grid'], ax=ax, axis_lims=axis_lims, show_grid=show_grid, title=title, credit=credit,
                                 back_ground_depth=back_ground_depth, back_ground_color_map=back_ground_color_map)

    plot_utilities.plot_release_points_and_polygons(stats_data, ax= ax, release_group=release_group)

    plot_utilities.show_particleNumbers(stats_data['total_num_particles_released'])
    plot_utilities.add_heading(heading)

    time_text = plt.text(.05, .05, '', transform=ax.transAxes,c='k', zorder=5)

    fig.tight_layout()

    anim = animation.FuncAnimation(fig, draw_frame, frames=stats_data[stats_data['time_var']].shape[0], interval=interval, blit=False)
    plot_utilities.animation_output(anim, movie_file, fps=fps, dpi=dpi)

    return anim

def animate_concentrations(concentration_data, plot_load=False,  axis_lims=None, credit=None, interval=100, colourbar=True,heading=None,
                     vmin=None, vmax=None,show_grid=False,title=None,logscale=False, cmap='viridis', shading=True,
                     movie_file= None, fps=15, dpi=300, back_ground_depth=True, back_ground_color_map= None):

    def draw_frame(nt):

        pc.set_array(data[nt, :])

        time_text.set_text(time_util.seconds_to_pretty_str(concentration_data['time'][nt],seconds=False))
        return pc, time_text

    fig = plt.gcf()
    ax = plt.gca()

    if plot_load:
        data_to_plot = concentration_data['load_concentration']
    else:
        data_to_plot = concentration_data['particle_concentration']

    vmin, vmax, data = plot_utilities._sort_colour_limits(data_to_plot, vmin, vmax, logscale, masking=back_ground_depth)

    print('animate_heat_map> colour axis limits',vmin,vmax)
    grid= concentration_data['grid']
    if shading:
        data = convert_face_to_nodal_values(concentration_data['grid']['x'], grid['triangles'], data)
        pc = ax.tripcolor(grid['x'][:,0], grid['x'][:,1], data[0,:],  triangles= grid['triangles'], zorder= 2, cmap=cmap,
                          vmin=vmin, vmax=vmax, edgecolors='none', shading='gouraud')
        interval=1
    else:
        pc = ax.tripcolor(grid['x'][:, 0], grid['x'][:, 1], facecolors=data[-1, :], triangles=grid['triangles'],
                          zorder=2, cmap=cmap, vmin=vmin, vmax=vmax, edgecolors='none')

    if axis_lims is None:    axis_lims=[np.min(grid['x'][:,0]),np.max(grid['x'][:,0]),np.min(grid['x'][:,1]),np.max(grid['x'][:,1])] # set axis limits to those of the grid

    plot_utilities.draw_base_map(grid, ax=ax, axis_lims=axis_lims, show_grid=show_grid, title=title, credit=credit,
                                 back_ground_depth=back_ground_depth, back_ground_color_map=back_ground_color_map)

    plot_utilities.plot_release_points_and_polygons(concentration_data, ax= ax)
    #plot_utilities.show_particleNumbers(data_to_plot['total_num_particles_released'])

    if colourbar: fig.colorbar(pc, ax=ax)

    time_text = plt.text(.05, .05, '', transform=ax.transAxes,c='k', zorder=5)
    plot_utilities.add_heading(heading)
    fig.tight_layout()

    anim = animation.FuncAnimation(fig, draw_frame, frames=concentration_data['time'].shape[0], interval=interval, blit=False)
    plot_utilities.animation_output(anim, movie_file, fps=fps, dpi=dpi)

    return anim

def plot_heat_map(stats_data,  release_group, nt=-1, axis_lims=None,show_grid=False, title=None,logscale=False, colour_bar= True,
                  var='count',vmin=None, vmax=None, credit=None, cmap='viridis', heading = None,
                  plot_file_name=None, back_ground_depth=True,back_ground_color_map= None):
    #todo repace var with data_to_plot=, as in other ploting code
    x,y, z = _get_stats_data(nt, stats_data, var, release_group, logscale)

    fig = plt.gcf()
    ax  = plt.gca()

    pc = ax.pcolormesh(x, y, z, shading='gouraud', cmap=cmap, zorder=2)
    if axis_lims is None:    axis_lims=[x[0],x[-1],y[0],y[-1]] # set axis limits to those of the grid

    plot_utilities.draw_base_map(stats_data['grid'], ax=ax, axis_lims=axis_lims, show_grid=show_grid, title=title, credit=credit,
                                 back_ground_depth=back_ground_depth, back_ground_color_map=back_ground_color_map)

    pc.set_clim(vmin, vmax)
    if colour_bar:
        plt.colorbar(pc, ax=ax)

    plot_utilities.plot_release_points_and_polygons(stats_data, release_group=release_group, ax=ax)

    plot_utilities.show_particleNumbers(stats_data['total_num_particles_released'])
    plot_utilities.add_heading(heading)

    fig.tight_layout()

    plot_utilities.show_output(plot_file_name= plot_file_name)

    return fig


def _get_stats_data(nt, d, var, release_group, logscale, zmin=None):
    # get count or variable patch Nan in zero counts
    # sum/average over all or 1 release group dim
    # nt is time step or age bin
    z= d[var][nt, :, :, :].astype(np.float64)
    count = d['count'][nt, :, :, :]

    # get ID of named release group
    release_groupID = d['release_groupID'][release_group]
    z = z[release_groupID, :, :]

    count = count[release_groupID, :, :]
    x = d['x'][release_groupID, :]
    y = d['y'][release_groupID, :]

    # make zero counts nan or zero and tose less than min value, so they won't plot
    if zmin is None:  zmin = np.nanmin(z)

    z[z < zmin] = np.nan
    z[count == 0] = np.nan

    if logscale:
        with np.errstate(all='ignore'):
            z = np.log10(z)
    return x, y, z


def plot_residence(residence_data, heading=None, plot_file_name=None):
    # time series of number resident in release polygon for each pulse

    fig = plt.gcf()
    ax  = plt.gca()
    ax.set_xlabel('Days since first pulse release')
    ax.set_ylabel('Number of each pulse residence in polygon')

    npulses= residence_data['count'].shape[1]
    t= (residence_data['time']-residence_data['time'][0])/3600/24.
    for npulse in range(npulses):
        d =residence_data['count'][:, npulse]
        i = (d > 0).argmax()
        ax.plot(t[i:],d[i:] )

    plot_utilities.add_heading(heading)

    plot_utilities.show_output(plot_file_name= plot_file_name)

    return plot_file_name
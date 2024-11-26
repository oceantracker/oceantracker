import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clr
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as font_manager
from oceantracker.definitions import node_types
from time import perf_counter

#from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

from matplotlib import animation
from oceantracker.util import time_util


color_palette={'land': (np.asarray([146, 179, 140])/256).tolist(), 'land_edge': [.5, .5, .5]}

def draw_base_map(grid, ax=plt.gca(), axis_lims=None, back_ground_depth=True,
                  show_grid=False, back_ground_color_map='Blues',axis_labels=False,
                  title=None, text1=None, credit=None):

    # get grid bounds to fill a rectangle, copes with node and grid values
    x = grid['x'][:, 0].ravel()
    y = grid['x'][:, 1].ravel()
    xbounds = np.asarray([np.min(x), np.max(x)])
    ybounds = np.asarray([np.min(y), np.max(y)])

    if axis_lims is None: axis_lims=np.concatenate((xbounds, ybounds))
    ax.set_xlim(axis_lims[:2])
    ax.set_ylim(axis_lims[2:])

    # fill outs domain as land
    mask_xy= grid['grid_outline']['domain_masking_polygon']
    ax.fill(mask_xy[:,0], mask_xy[:,1],
          edgecolor= None, facecolor=color_palette['land'], linewidth=.5, zorder=0)
    #
    ax.plot(mask_xy[:, 0], mask_xy[:, 1])

    # plot islands from outline
    for g in grid['grid_outline']['islands']:
            ax.fill(g['points'][:, 0], g['points'][:, 1], edgecolor=color_palette['land_edge'],
                    facecolor=color_palette['land'], linewidth= 0.5, zorder= 3)

    if 'water_depth' in grid and back_ground_depth:
        plot_coloured_depth(grid, ax=ax,color_map= back_ground_color_map,zorder=0)

    if show_grid:
        ax.triplot(grid['x'][:, 0], grid['x'][:, 1], grid['triangles'], color=(0.8, 0.8, 0.8), linewidth=.5, zorder=1)

    sel = grid['node_type'] == node_types.open_boundary# open_boundary_nodes
    plt.scatter(grid['x'][sel, 0], grid['x'][sel, 1],s= 4,marker= '.',c='darkgreen', zorder=1)

    if not axis_labels:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
    ax.tick_params(axis="both", direction="in", right=True, top=True)

    if title is not None:  ax.set_title(title)
    if text1 is not None:  text_norm(.4, .1, text1, fontsize=8)
    add_credit(credit)
    add_map_scale_bar(axis_lims, ax=ax)
    return ax

def display_grid(grid, ginput=0, axis_lims=None):
    # for checking nad choosing release

    draw_base_map(grid, show_grid=True, axis_lims=axis_lims)
    if 1==0:
        bt = np.flatnonzero(grid['is_boundary_triangle']==1)
        plt.plot(grid['x'][grid['triangles'][bt,:],0].T, grid['x'][grid['triangles'][bt,:],1].T,'r', zorder=9)

    if ginput > 0:
        p =plt.gcf().ginput(n=ginput)

        print('ginput coords ')
        print(str(np.asarray(p).tolist()))

    plt.show()


def plot_field(grid, field_vals, ax=plt.gca(), color_map=None, vmin=None, vmax=None, zorder=3):
    # use tri surf to color map field in 3D, defaul view is 2D from above

    pc = ax.tripcolor(grid['x'][:,0], grid['x'][:,1], field_vals, triangles=grid['triangles'],
                  shading='gouraud', cmap=color_map, edgecolors='none',
                  vmin=vmin, vmax=vmax, zorder=zorder)
    return pc

def plot_coloured_depth(grid, ax=plt.gca(), color_map=None, zorder=3):
    # find depth range inside axes to set max  and min depth

    # plot colored depth, but dilute deepest colour but setting vmax 20% larger, to set colormap limits based on nodes inside axies
    sel =  np.logical_and(grid['x'][:, 0] >= ax.get_xlim()[0],  grid['x'][:,0] <= ax.get_xlim()[1])
    sel = np.logical_and(sel, grid['x'][:, 1] >= ax.get_ylim()[0])
    sel = np.logical_and(sel, grid['x'][:, 1] <= ax.get_ylim()[1])

    sel = np.logical_and(sel, grid['node_type']== 0) # only look at water nodes, as in regular grid some nodes are not used in triagle grod

    depth = grid['water_depth']
    vmax = np.nanmax(depth[sel])

    # blue particle can be lost in deep water, cant get alphaand  not to draw grid edges, so outscale deepest colour
    if color_map is None:
        color_map = 'Blues'
        vmax=1.3*vmax

    plot_field(grid, depth, ax=ax, color_map=color_map, vmin= 0., vmax=vmax, zorder=zorder)

def plot_dry_cells(track_data,show_dry_cells=True, nt=0):

    grid = track_data['grid']
    cmap = clr.LinearSegmentedColormap.from_list('custom sand', ['#FFFFFF', '#cba254'], N=128)

    if show_dry_cells and 'dry_cell_index' in track_data :
        dry_cell_data = track_data['dry_cell_index'].copy().astype(np.float32)
        dry_cell_data[dry_cell_data < 128] = np.nan
        pc = plt.gca().tripcolor(grid['x'][:, 0], grid['x'][:, 1], facecolors=dry_cell_data[nt, :], triangles=grid['triangles'],
                                 zorder=3, vmin=128, vmax=255, edgecolors='none', alpha=.3, cmap=cmap, antialiaseds=True)
    else:
        # small fast dummy plot
        dry_cell_data = np.full((track_data['time'].shape[0],1),np.nan)
        pc = plt.gca().tripcolor(grid['x'][:3, 0],  grid['x'][:3, 1], grid['triangles'][0,:],
                                 zorder=3, vmin=128, vmax=255, edgecolors='face', alpha=0.)

    return pc, dry_cell_data


def plot_release_points_and_polygons(d, release_group=None, ax = plt.gca(), color=[.3,.3,.3]):
    # release_group is 1 based
    if release_group is None :
        # plot all release groups
        sel = d['particle_release_groups'].keys()

    else:
        sel= [release_group]
    objs=[]
    for name in sel:
        rg = d['particle_release_groups'][name]
        p = rg['points'][:,:2]
        if rg['release_type'] == 'polygon':
            o = ax.plot(p[:, 0], p[:, 1], '-', color=color,zorder=8, linewidth=1)
        else:
            # for grid and points releases
            o = ax.plot(p[:, 0], p[:, 1], 'x', color=color, markersize=6,zorder=9)

        objs.append(o)
    return objs

def draw_polygon_list(polylist, ax=plt.gca(), color =[.2, .8, .2]):
    if polylist is not None:
        for p in  polylist:
            xy= np.asarray(p['points'])
            xy= np.vstack((xy,xy[0,:])) # ensure its closed
            ax.plot(xy[:, 0], xy[:, 1], '-', color=color, linewidth=1, zorder=4)

def _sort_colour_limits(data, vmin, vmax, log_scale, masking = True):

    data_out = data.copy().astype(np.float64)
    vmin = np.nanmin(data_out) if vmin is None else vmin
    vmax = np.nanmax(data_out) if vmax is None else vmax

    data_out[data_out < vmin]= np.nan # mask those too small

    if log_scale:
        sel = data <= 0
        if sel.size > 0:
            print(' Using log scaling of data, some values <= 0, masking these values')
            data_out[sel] = np.nan  # mask zero values
        data_out = np.log10(data_out) # use a copy to preserve data
        vmin = np.nanmin(data_out) if vmin <= 0  else np.log10(vmin)
        vmax = np.nanmax(data_out) if vmax <= 0  else np.log10(vmax)

    if masking:
        data_out[np.isnan(data_out)] = vmin # gives same color to all <= vmin

    return vmin, vmax, data_out

def  text_norm(x,y,s,fontsize=5):
    ax= plt.gca()
    ax.text(x, y,s, fontsize=fontsize, transform=ax.transAxes)

def add_heading(txt):
    if txt is not None:
        text_norm(.025, .95, txt, fontsize=6)

def add_map_scale_bar(axis_lims, ax=plt.gca(),x_size_fraction=10 ):
    dx= axis_lims[1]- axis_lims[0]
    ds = np.power(10, max(np.floor(np.log10(dx / x_size_fraction)),1))
    lab = '%1.0f m' % ds if ds < 1000 else  '%1.0f km' % (ds/1000)
    fontprops = font_manager.FontProperties(size=8)
    scalebar = AnchoredSizeBar(ax.transData,
                               ds, lab,
                               'lower center',
                               pad=0.2,
                               color='black',
                               frameon=False,
                               size_vertical = .005,
                               label_top=False,
                               fontproperties=fontprops)

    ax.add_artist(scalebar)
#def add_time_text(t): time_text.set_text(time_util.seconds_to_pretty_str(t,seconds=False))

def show_particleNumbers(n):  text_norm(.71, .04, '%3.0f Particles' % n, fontsize=5)

def add_credit(s):  text_norm(.71, .015,'OceanTracker- R. Vennell, 2024' if s is None else s, fontsize=5)

def show_output(plot_file_name=None, ):
    if plot_file_name is not None:
        plt.savefig(plot_file_name,dpi=300)

    plt.show()
    plt.close()  # prevents over plotting

def animation_output(anim, movie_file, fps = 15, dpi=600,show=True):

    if show :    plt.show()
    if movie_file is not None:
        t0 = perf_counter()
        print('Building movie:  ' + movie_file)
        try:
            FFMpegWriter = animation.writers['ffmpeg']
        except Exception as e:
            print('OceanTracker post_processing error: could not make movie as ffmpeg no installed or other error initialising ffmpeg')
            print('           Install ffmpeg??, doing screen plot instead')
            plt.close()
            return

        metadata = dict(title='OceanTracker  Demo', artist='Matplotlib')
        writer = FFMpegWriter(fps=fps, metadata=metadata)
        anim.save(movie_file, writer=writer, dpi=dpi)

        plt.close() # prevents over plotting
        print(f'finished writing file, time={(perf_counter()-t0)/60} minutes')


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clr
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as font_manager

from oceantracker.util.triangle_utilities_code import convert_face_to_nodal_values

from oceantracker.post_processing.read_output_files import load_output_files
#from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

from matplotlib import animation
from oceantracker.util import time_util

color_palette={'land': (np.asarray([146, 179, 140])/256).tolist(), 'land_edge': [.5, .5, .5]}

def draw_base_map(grid, ax=plt.gca(), axis_lims=None, back_ground_depth=True,
                  show_grid=False, back_ground_color_map='Blues', title=None, text1=None, credit=None):

    # get grid bounds to fill a recgtangle
    bounds= [np.min(grid['x'][:, 0]), np.max(grid['x'][:, 0]), np.min(grid['x'][:, 1]), np.max(grid['x'][:, 1])]
    dx,dy = bounds[1]- bounds[0], bounds[3]- bounds[2]
    f= 0.05
    bounds =np.asarray([ [bounds[0]-f*dx, bounds[1]+f*dx], [bounds[2]-f*dy,  bounds[3]+f*dy]]) # l
    b = np.asarray([bounds[0,:], [bounds[1,0], bounds[0,1] ], bounds[1, :], [bounds[0,0],bounds[1,1] ], bounds[0,:] ] )

    # fill background land retangle
    ax.fill(b[:,0] , b[:, 1],  facecolor=color_palette['land'],  zorder=0)

    if axis_lims is None: axis_lims= bounds.flatten().tolist()
    ax.set_xlim(axis_lims[:2])
    ax.set_ylim(axis_lims[2:])

    # fill domain as white
    ax.fill(grid['grid_outline']['domain']['points'][:,0], grid['grid_outline']['domain']['points'][:,1],
            edgecolor= None, facecolor=(1., 1., 1.), linewidth=.5, zorder=0)

    # plot islands from outline
    for g in grid['grid_outline']['islands']:
            ax.fill(g['points'][:, 0], g['points'][:, 1], edgecolor=color_palette['land_edge'],
                    facecolor=color_palette['land'], linewidth= 0.5, zorder= 3)
    ax.plot(grid['grid_outline']['domain']['points'][:, 0], grid['grid_outline']['domain']['points'][:, 1], c=color_palette['land_edge'], linewidth=0.5, zorder=3)

    if  back_ground_depth:
        plot_coloured_depth(grid, ax=ax,color_map= back_ground_color_map,zorder=1)

    if show_grid:
        ax.triplot(grid['x'][:, 0], grid['x'][:, 1], grid['triangles'], color=(0.8, 0.8, 0.8), linewidth=.5, zorder=1)

    sel = grid['node_type'] == 3 # open_boundary_nodes
    plt.scatter(grid['x'][sel, 0], grid['x'][sel, 1],s= 4,marker= '.',c='darkgreen')

    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(axis="both", direction="in", right=True, top=True)

    if title is not None:  ax.set_title(title)
    if text1 is not None:  text_norm(.4, .1, text1, fontsize=8)
    add_credit(credit)
    add_map_scale_bar(axis_lims, ax=ax)
    return grid

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
    # use tri surf to color map feild in 3D, defaul view is 2D from above

    pc = ax.tripcolor(grid['x'][:,0], grid['x'][:,1], field_vals, triangles=grid['triangles'],
                  shading='gouraud', cmap=color_map, edgecolors='none',
                  vmin=vmin, vmax=vmax, zorder=zorder)
    return pc

def plot_coloured_depth(grid, ax=plt.gca(), color_map=None, zorder=3):
    # find depth range inside axes to set max  and min depth

    # plot colored depth, but dilute deepest colour but setting vmax 20% larger, to set colormap limits based on nodes inside axies
    sel =  np.logical_and(grid['x'][:,0] >= ax.get_xlim()[0],  grid['x'][:,0] <= ax.get_xlim()[1])
    sel = np.logical_and(sel, grid['x'][:, 1] >= ax.get_ylim()[0])
    sel = np.logical_and(sel, grid['x'][:, 1] <= ax.get_ylim()[1])
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


def plot_release_points_and_polygons(d, release_group=None, ax = plt.gca(), color =[.2, .8, .2]):
    # release_group is 1 based
    if release_group is None :
        sel= range(len(d['particle_release_group_info'])) # show all
    else:
        sel = [release_group-1]

    for n in sel:

        rg = d['particle_release_group_info'][n]
        p = np.asarray(rg['points'])
        if 'user_polygonID' in rg:
            ax.plot(p[:, 0], p[:, 1], '-', color=color,zorder=8, linewidth=1)
        else:
            ax.plot(p[:, 0], p[:, 1], '.', color=color, markersize=10,zorder=14)

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

def add_map_scale_bar(axis_lims, ax=plt.gca()):
    dx= axis_lims[1]- axis_lims[0]
    ds = np.power(10, np.floor(np.log10(dx / 10)))
    lab = '%1.0f m' % ds if ds < 1000 else  '%1.0f km' % (ds/1000)
    fontprops = font_manager.FontProperties(size=8)
    scalebar = AnchoredSizeBar(ax.transData,
                               ds, lab,
                               'lower center',
                               pad=0.2,
                               color='black',
                               frameon=False,
                               size_vertical = 1,
                               label_top=False,
                               fontproperties=fontprops)

    ax.add_artist(scalebar)
#def add_time_text(t): time_text.set_text(time_util.seconds_to_pretty_str(t,seconds=False))

def show_particleNumbers(n):  text_norm(.71, .04, '%3.0f Particles' % n, fontsize=5)

def add_credit(s):  text_norm(.71, .015,'OceanTracker- R. Vennell, 2022' if s is None else s, fontsize=5)

def show_output(plot_file_name=None, ):
    if plot_file_name is not None:
        plt.savefig(plot_file_name,dpi=300)

    plt.show()
    plt.close()  # prevents over plotting

def animation_output(anim, movie_file, fps = 15, dpi=300,show=True):

    if show :    plt.show()
    if movie_file is not None:
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

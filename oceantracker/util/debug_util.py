import matplotlib.pyplot as plt

import sys, gc
from oceantracker.interpolator.util import triangle_interpolator_util
import numpy as np

def plot_grid(grid):
    plt.triplot(grid['x'][:,0],grid['x'][:,1],grid['triangles'],c=[.8,.8,.8])

def plot_points(x,m='.', c='r'):
    plt.scatter(x[:,0],x[:,1],c=c,marker=m)

def plot_line(x, c='b'):
    plt.plot(x[:,0],x[:,1],c=c)

def show():
    plt.show(block=False)

def check_walk_step(grid, part_prop, active,msg_logger, tol = 1.E-2, crumbs=None):
    x= part_prop['x'].data[active,:]
    n_cell = part_prop['n_cell'].data[active]

    #check bc cords
    #triangle_interpolator_util.get_cell_cords_check()
    bc = triangle_interpolator_util.get_cell_cords_check(grid['bc_transform'],x,n_cell)
    sel =np.logical_or( np.any(bc < -tol, axis =1), np.any(bc > 1.+tol, axis =1))
    if np.any(sel):
        msg_logger.msg(f'Cell search,  some x not in triangle for  {np.count_nonzero(sel)} of  {active.size} ,bc tolerance={tol:.2e}', crumbs=crumbs)

    return active[sel]

def plot_walk_step(x_new,grid, part_prop, sel=np.zeros((1,),dtype=np.int32)):
    if sel.size==0 : return
    x = part_prop['x'].data
    x0 = part_prop['x_last_good'].data
    n_cell = part_prop['n_cell'].data
    n_cell_last_good = part_prop['n_cell_last_good'].data
    tri = grid['triangles']

    plt.triplot(grid['x'][:,0],grid['x'][:,1],tri,c=[.8,.8,.8])
    #plt.triplot(grid['x'][:, 0], grid['x'][:, 1], tri[grid['dry_cell_index'] > 128, :], c=[0,  0,.8])


    plt.triplot(grid['x'][:, 0], grid['x'][:, 1], tri[n_cell[sel], :], c=[.8, 0, 0.], lw=3)

    plt.triplot(grid['x'][:, 0], grid['x'][:, 1], tri[n_cell_last_good[sel],:], c=[0, .8,0.], lw=1)

    plt.plot(  x_new[sel,0],  x_new[sel,1],'go')

    plt.plot(x[sel,0],x[sel,1],'rx')
    plt.show(block=True)
    pass

def check_cells_correct(grid,part_prop, active, tol=1e-2):
    x= part_prop['x'].data
    n_cell = part_prop['n_cell'].data
    status= part_prop['status'].data
    tri = grid['triangles']

    from oceantracker.interpolator.util.triangle_interpolator_util import get_cell_cords_check

    bc = get_cell_cords_check(grid['bc_transform'],x,n_cell)
    sel = np.logical_or(np.any(bc[active,:] > 1+tol,axis=1), np.any(bc[active,:]  <-tol,axis=1))
    sel= active[sel]

    if sel.size>0:
        print('ncell not right, number=', sel.size,'of',active.size)
        print(bc[sel, :])
        print(status[sel])
        n = sel[0]
        xn=x[n,:]
        x1=grid['x'][tri[n_cell[n],:], 0]
        x2 = grid['x'][tri[n_cell[n], :], 1]
        print(x1 - xn[0])
        print(x2 - xn[1])
        pass
def get_referers(o):
   return sys.getrefcount(o)

def print_referers(o,tag=''):
    refs =gc.get_referrers(o)
    for n, l in enumerate(refs):
        print(tag,n, type(l))

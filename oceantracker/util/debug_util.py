import matplotlib.pyplot as plt
import matplotlib
#matplotlib.use('TkAgg')
matplotlib.use('Qt5Agg')
import sys, gc

def plot_grid(grid):
    plt.triplot(grid['x'][:,0],grid['x'][:,1],grid['triangles'],c=[.8,.8,.8])

def plot_points(x,m='.', c='r'):
    plt.scatter(x[:,0],x[:,1],c=c,marker=m)

def plot_line(x, c='b'):
    plt.plot(x[:,0],x[:,1],c=c)

def show():
    plt.show(block=False)


def get_referers(o):
   return sys.getrefcount(o)

def print_referers(o,tag=''):
    refs =gc.get_referrers(o)
    for n, l in enumerate(refs):
        print(tag,n, type(l))

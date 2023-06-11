import matplotlib.pyplot as plt
import matplotlib
#matplotlib.use('TkAgg')
matplotlib.use('Qt5Agg')


def plot_grid(grid):
    plt.triplot(grid['x'][:,0],grid['x'][:,1],grid['triangles'],c=[.8,.8,.8])

def plot_points(x,m='.', c='r'):
    plt.scatter(x[:,0],x[:,1],c=c,marker=m)

def plot_line(x, c='b'):
    plt.plot(x[:,0],x[:,1],c=c)

def show():
    plt.show(block=False)
import numpy  as np

def make_regular_grid(xy_center,grid_size,grid_span):
    # regular grid, where columns are x, rows are y
    base_x = xy_center[0] + np.linspace(-grid_span[0] / 2., grid_span[0] / 2., grid_size[1]).reshape(-1, 1)
    base_y = xy_center[1] + np.linspace(-grid_span[1] / 2., grid_span[1] / 2., grid_size[0]).reshape(-1, 1)
    xi, yi= np.meshgrid(base_x,base_y)

    return xi, yi, get_bounding_box(xi,yi )

def get_bounding_box(x_grid,y_grid):
    bounding_box_ll_ul = np.asarray([[x_grid[0, 0], y_grid[0, 0]], [x_grid[0, -1], y_grid[-1, 0]]], dtype=np.float64)
    return bounding_box_ll_ul
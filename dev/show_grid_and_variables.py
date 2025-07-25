from matplotlib import pyplot as plt
from oceantracker.util.ncdf_util import NetCDFhandler

n_case= 0
match n_case:
    case 0:
        # hauraki gulf
        file_name= r'Z:\Hindcasts\NorthIsland\2024_hauraki_gulf_auck_uni\2020\01\schout_1.nc'
        x_var= 'SCHISM_hgrid_node_x'
        y_var = 'SCHISM_hgrid_node_y'
        tri_var= 'SCHISM_hgrid_face_nodes'
        depth_var= 'depth'
        one_based = True
        vmax= 30


nc = NetCDFhandler(file_name)
for key, item in nc.variable_info.items():
    print(key,':', item)

x = nc.read_variable(x_var)
y = nc.read_variable(y_var)
tri = nc.read_variable(tri_var) - one_based
depth = nc.read_variable(depth_var)

plt.tripcolor(x, y, tri[:, :3], depth, vmax=vmax)
plt.triplot(x, y, tri[:, :3], lw=.5, c=[.8,.8,.8])
plt.colorbar()
plt.show()

pass
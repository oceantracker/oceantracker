from oceantracker.util.ncdf_util import NetCDFhandler
from os import path
import numpy as np
from  matplotlib import  pyplot as plt
import glob

source=1
if  source ==1:
        data_file_mask =r'C:\data\MS2017\schism_marl2017010?_00z_3D.nc'
        ax=    1.0e+06 *np.asarray([ 1.5903,    1.6026,    5.4795,    5.501]) # abel tasman
        out_file_base='demo_hindcast_schisim'
        nz0=22
        nt_step=2
        n_files=3

# find sub domain
file_list=glob.glob(data_file_mask)
for n_file, fn in enumerate(file_list[:n_files]):
    d = NetCDFhandler(fn)
    print(fn)
    v= d.read_variables(['SCHISM_hgrid_node_x','SCHISM_hgrid_node_y','SCHISM_hgrid_face_nodes'])
    x,y = v['SCHISM_hgrid_node_x'], v['SCHISM_hgrid_node_y']
    tri = v['SCHISM_hgrid_face_nodes']
    # find  triangles in sub domain
    x_tri= np.mean(x[tri[:,:3]-1],axis=1)
    y_tri= np.mean(y[tri[:,:3]-1],axis=1)

    sel_tri= np.logical_and.reduce((x_tri >  ax[0] ,   x_tri <  ax[1], y_tri >  ax[2] ,  y_tri <  ax[3]))
    sel_tri = np.flatnonzero(sel_tri)

    required_tri= tri[sel_tri,:]
    sel_nodes=np.unique(required_tri)
    sel_nodes= sel_nodes[sel_nodes >=0]
    new_tri = np.zeros((sel_tri.shape[0],4),np.int32)
    for n, val in enumerate(sel_nodes.tolist()):
        sel = int(val) == required_tri # where tri matches the required nodes
        new_tri[sel]= n + 1

    new_tri[required_tri[:,3] ==-99999,3] = -99999 # make missing 4th values the same


    # write file

    comp = 4
    nodes =sel_nodes-1
    out_file= f'{out_file_base}{n_file+1:02d}.nc'
    nc = NetCDFhandler(out_file,mode='w')
    nc.write_a_new_variable('SCHISM_hgrid_face_nodes', new_tri,  d.all_var_dims('SCHISM_hgrid_face_nodes'))

    # write attributes
    for name,val in d.global_attrs().items():
        nc.write_global_attribute(name,val)

    # transphere simple nodal variables
    for var in ['SCHISM_hgrid_node_x','SCHISM_hgrid_node_y','depth']:
        vals= d.read_a_variable(var)[nodes]
        dims= d.all_var_dims(var)
        nc.write_a_new_variable(var,vals,dims)

    #
    nc.write_a_new_variable('time', d.read_a_variable('time')[::nt_step],  d.all_var_dims('time'),attributes=d.all_var_attr('time'))
    nc.write_a_new_variable('wetdry_elem', d.read_a_variable('wetdry_elem')[::nt_step, sel_tri],  d.all_var_dims('wetdry_elem'),compressionLevel=comp)

    # transphere 3D variable values
    nc.write_a_new_variable('node_bottom_index', d.read_a_variable('node_bottom_index')[nodes]-nz0,  d.all_var_dims('node_bottom_index'))

    for var in ['zcor','dahv','elev','hvel','vertical_velocity','temp','diffusivity']:
        print('writing:', var)
        if d.is_var_dim(var,'nSCHISM_vgrid_layers'):
            vals= d.read_a_variable(var)[::nt_step, nodes,nz0:,...] # 3D
        else:
            vals = d.read_a_variable(var)[::nt_step, nodes, ...]  #2D

        dims = d.all_var_dims(var)
        a = d.all_var_attr(var)

        if True:
            s= 2**16
            vals[vals== d.var_attr(var,'missing_value')] = np.nan
            vmin = np.nanmin(vals)
            vmax = np.nanmax(vals)
            vals[np.isnan(vals)] = vmin

            # scale into 0-255 range
            scalefactor = float(vmax - vmin) / (2**16-1)
            offset = float(vmin)
            vals = (vals-offset) / scalefactor
            vals = np.round(vals)

            vals = vals.astype(np.uint16)
            a.pop('missing_value')
            a.update(dict(add_offset=offset, scale_factor=scalefactor))
            print('limits:', var, vmin, vmax,scalefactor,offset)

        nc.write_a_new_variable(var,vals,dims,compressionLevel=comp,attributes=a)

    d.close()
    nc.close()

# read and plot
r = NetCDFhandler(out_file)
var = r.read_variables(r.all_var_names())

plt.triplot(var['SCHISM_hgrid_node_x'],var['SCHISM_hgrid_node_y'],var['SCHISM_hgrid_face_nodes'][:,:3]-1)

plt.show()

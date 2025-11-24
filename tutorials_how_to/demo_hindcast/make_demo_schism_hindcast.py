from oceantracker.util.ncdf_util import NetCDFhandler
from os import path
import numpy as np
from  matplotlib import  pyplot as plt
import glob
import xarray as xr
import random, string
import argparse
from copy import deepcopy
def compute_scale_and_offset_int16(data, missing_value=None):
    # scale data into int32's
    # mask and get min
    if missing_value is not None:
        data[data == missing_value] = np.nan
    dmin, dmax = np.nanmin(data), np.nanmax(data)

    # int 16 negative 32768 through positive 32767
    # stretch/compress data to the available packed range
    i16 =np.iinfo(np.int16)

    i16_range = float(i16.max - 1)  # range with last value reserved for missing value

    add_offset   = (dmin+.5*(dmax-dmin)).astype(data.dtype)
    scale_factor = ((dmax - add_offset)/i16_range).astype(data.dtype)

    # translate the range to be symmetric about zero


    # mask with new missing value
    missing_value = i16.max
    #data[np.isnan(data)] = missing_value
    #data = np.round(data,0).astype(np.int16)
    return scale_factor, add_offset, missing_value

def write_file(ds_in,n_file, nodes,sel_tri, tri, is3D=False):
    # get subset of hindcast  write
    print('is3D=',is3D)

    # write 2D file

    sel_time = range(0, ds_in.dims['time'],2)

    node_bottom_index = ds_in['node_bottom_index'][nodes].compute()

    # select every second depth and all cells at water depth / bottom of model
    nz = ds_in.dims['nSCHISM_vgrid_layers']
    sel_z= np.arange(node_bottom_index.min(), nz,2) # start 1 above smallest botom cell w( which si one
    sel_z = np.append(np.sort(np.unique(node_bottom_index))- 1,sel_z ,axis=0)


    ds_out = ds_in.isel(time=sel_time, nSCHISM_hgrid_node=nodes, nSCHISM_vgrid_layers=sel_z).compute()

    if not is3D:
        # drop 3d variables
        for name, v in ds_out.variables.items():
            if 'nSCHISM_vgrid_layers' in v.dims and not is3D:
                ds_out = ds_out.drop_vars(name)

    ds_out = ds_out.isel(nSCHISM_hgrid_face=sel_tri)


    ds_out['node_bottom_index'] = (ds_out['node_bottom_index'] - node_bottom_index+1).astype(np.int32)

    # make row 1049 a quad cell and delete next row
    nn=1049
    tri =tri.copy()
    tri[nn,:]= [625,636,635,621]
    tri= np.vstack((tri[:nn-1,:],tri[nn:,:] ))
    sel = np.full((sel_tri.size,),True)
    sel[nn]= False # drop one

    e={}
    for name, v in ds_out.variables.items():
        if 'nSCHISM_hgrid_node' in v.dims and (v.dtype == np.float32 or v.dtype == np.float64):
            scale_factor, add_offset, missing_value =compute_scale_and_offset_int16(v, missing_value=None)
            e[name] = dict(scale_factor=scale_factor, add_offset=add_offset, missing_value=missing_value, dtype=np.int16,
                           zlib=True, complevel=9
                           )

    ds_out = ds_out.isel(nSCHISM_hgrid_face=sel)
    ds_out['SCHISM_hgrid_face_nodes'][:,:] = tri.astype(np.int32)
    ds_out['SCHISM_hgrid_face_nodes'] = ds_out['SCHISM_hgrid_face_nodes'].astype(np.int32)
    return ds_out, e, n_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A simple script to greet a user.")
    # 2. Add arguments
    # Positional argument: 'name'
    parser.add_argument("name", help="The name of the user to greet.")

    data_file_mask =r'Z:\Hindcasts\UpperSouthIsland\2020_MalbroughSounds_10year_benPhD\2017\schism_marl201701*_00z_3D.nc'
    ax=    1.0e+06 *np.asarray([ 1.5903,    1.6026,    5.4795,    5.501]) # abel tasman
    out_file_base='demo_hindcast_schisim'
    out_dir = path.dirname(__file__)
    nz0=22
    nt_step=2
    n_files=0

    out_file_2D =[]
    # find sub domain
    file_list=glob.glob(data_file_mask)
    for n_file, fn in enumerate(file_list[:n_files]):

        ds_in= xr.open_dataset(fn, chunks=dict(time=1),
                               drop_variables=['SCHISM_hgrid_edge_nodes', 'edge_bottom_index','ele_bottom_index', 'salt',
                                               'TKE','mixing_length',
                                   'SCHISM_hgrid_edge_x', 'SCHISM_hgrid_edge_y', 'SCHISM_hgrid_face_x', 'SCHISM_hgrid_face_y'])
        x,y = ds_in['SCHISM_hgrid_node_x'].compute().data, ds_in['SCHISM_hgrid_node_y'].compute().data
        tri = ds_in['SCHISM_hgrid_face_nodes'].compute().data.astype(np.int32)

        # find  triangles in sub-domain
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

        new_tri[required_tri[:,3] ==-99999,3] = -99 # make missing 4th values the same
        nodes = sel_nodes - 1


        if n_file < 1:
            out_file3D = path.join(out_dir, 'schsim3D', f'{out_file_base}3D_{n_file:02d}.nc')
            print(out_file3D)
            ds_out,e, n_file =write_file(ds_in,n_file, nodes, sel_tri, new_tri, is3D=True)
            ds_out.to_netcdf(out_file3D,encoding=e)

        # keep 2D copy to write in random order
        out_file_2D.append(write_file(ds_in, n_file, nodes, sel_tri, new_tri, is3D=False))

    # random ise name
    random.shuffle(out_file_2D)
    tag = np.random.choice(np.arange(len(out_file_2D)), size=len(out_file_2D), replace=False)
    for ds,e,n_file in out_file_2D:

        out_file = path.join(out_dir,'schsim2D', f'Random_order_{tag[n_file]:02d}_schsim2D_{n_file}.nc')
        print(out_file)
        ds.to_netcdf(out_file, encoding=e)

    # read and plot
    print('reading',out_file3D)
    r = NetCDFhandler(out_file3D)
    var = r.read_variables(r.all_var_names())
    x, y =var['SCHISM_hgrid_node_x'],var['SCHISM_hgrid_node_y']

    plt.scatter(x, y, c='k',zorder=0,s=6)

    tri = var['SCHISM_hgrid_face_nodes']
    nn= tri[:, 3]> 1
    nodes=  tri[nn,:][0]
    plt.plot(x[nodes-1], y[nodes-1] ,c='g',zorder=9)

    sel=tri[:, 3] < 1
    plt.triplot(x, y, tri[sel,:3]-1,lw=.5)

    xn=x[nodes-1]
    yn=y[nodes-1]
    print(nodes,xn, yn)
    #plt.triplot(x, y,  tri[nn,:3]-1,c='k')
    plt.scatter(xn, yn ,c='r')


    for node in nodes:
        plt.text(x[node-1],y[node-1],str(int(node)))
        pass

    # make hgrid file

    plt.show()


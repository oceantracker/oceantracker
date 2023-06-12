import  numpy as np
from numba import njit
from oceantracker.util.ncdf_util import NetCDFhandler
from os import  path

def convert_to_rectangular(file_name,time_chunk=24):
    # convert a compact file to rectangular format
    nc_in = NetCDFhandler(file_name, mode='r')

    # open converted file
    ff = path.split(file_name)
    fn_out= path.join(ff[0],ff[1].replace('_compact.','_rectangular.'))
    nc_out = NetCDFhandler(fn_out, mode='w')

    nc_in.copy_global_attributes(nc_out)

    # get list of time_part var and copy others to new file
    time_part_vars=[]
    for name in nc_in.get_var_names():
        if name not in ['write_step_index', 'time_step_range']:
            if  nc_in.is_var_dim(name, 'time_particle_dim'):
                time_part_vars.append(name)
            else:
                nc_in.copy_variable(nc_out, name)

    # now create time_part. vars
    nc_out.add_dimension('time_dim',None)
    n_released= nc_in.file_handle.total_num_particles_released
    for name in time_part_vars:
        v = nc_in.file_handle[name]
        dims = ['time_dim']+[x.replace('time_particle_dim', 'particle_dim') for x in v.dimensions]
        chunks= [time_chunk,n_released]

        # if a vector extend chunking
        if len(v.dimensions) == 2:chunks += [len(v.dimensions)]
        nc_out.create_a_variable(name,dims, v.dtype, description=v.description, chunksizes=chunks)

    # now read time steps
    for nt, b in enumerate(nc_in.get_var_data('time_step_range')):
            sel= np.arange(b[0], b[1])  # range for this time step
            rows = nc_in.read_a_variable('write_step_index', sel)
            cols= nc_in.read_a_variable('particle_ID',sel)

            for name in time_part_vars:
                _read_compact_var_time_step(nc_in, name, sel,nt, cols, out=nc_out.file_handle.variables[name][nt,...])

                #_filIinDeadParticles(d['status'], 'status', d['status'], -127)

    nc_in.close()
    nc_out.close()
    return fn_out

def _read_compact_var_time_step(nc, var_name, sel,nt,  cols, out=None):

    if out is None:
        s = nc.get_var_shape(var_name)
        num_released = nc.get_global_attr('total_num_particles_released')
        data= np.full((sel.size, num_released) + tuple(s[1:]),
                      nc.get_var_fillValue(var_name), dtype=nc.get_var_dtype(var_name))
    else:
        data = out

    d = nc.file_handle.variables[var_name][sel,...]
    # inset one time step
    _insertMatrixValues(d,cols, data)

    return  data


    _filIinDeadParticles(d['status'], 'status', d['status'], -127) # do status last as needed to work on others


    return d

#@njit
def _insertMatrixValues(x,col,values):
    for n in range(values.shape[0]):
        x[col[n],...] = values[n]

@njit
def _filIinDeadParticles(data, var, status, missing_status):
    # fill in values after death with last good one
    for m in range(data.shape[1]):
        n_last_write= 0
        for n in range(data.shape[0]):
            if status[n,m]  != missing_status:
                n_last_write  = n  #  find last good value, before particle is marked dead
            else:
                if var == 'status':
                    # no status once no longer been written is unknown, so make dead
                    data[n, m] = -2  # set as dead as read status unknown
                else:
                    data[n,m,...] =  data[n_last_write,m,...]
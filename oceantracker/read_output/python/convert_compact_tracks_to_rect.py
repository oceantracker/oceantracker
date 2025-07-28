from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.read_output.python import read_ncdf_output_files
from os import path
import  numpy as np
from numba import njit
from time import perf_counter
from oceantracker.shared_info import shared_info as si

def convert_compact_file(file_name1):
    # particles with greater than stats val are not return
    nc1 = NetCDFhandler(file_name1, mode='r')
    particleID = nc1.read_variable('particle_ID')
    ID = nc1.read_variable('ID')

    file_name2= path.join(path.dirname(file_name1),
                          path.basename(file_name1).replace('_compact_','_rectangular_'))
    nc2 = NetCDFhandler(file_name2, mode='w')
    nc1.copy_global_attributes(nc2)
    nc2.create_dimension('time_dim', nc1.dim('time_dim'))
    nc2.create_dimension('particle_dim', ID[-1] - ID[0] + 1)
    time_step_range = nc1.read_variable('time_step_range')

    for name, var in nc1.file_handle.variables.items():
        if name in ['particle_ID', 'write_step_index',b'time_step_range']: continue

        if 'time_particle_dim' in var.dimensions:
            _write_time_depend_part_prop (name,nc1,nc2,particleID,ID, time_step_range)
        elif 'particle_dim' in var.dimensions:
            _write_non_time_depend_part_prop(name, nc1, nc2, ID)
        else:
            nc1.copy_variable(name,nc2)

    return file_name2


def _write_time_depend_part_prop(name, nc1, nc2, particleID, ID, time_step_range):

    vi = nc1.variable_info[name]
    dims=[]
    s=[]
    for dim in vi['dims'][1:]:
        nc2.create_dimension(dim, vi['sizes'][dim])
        dims.append(dim)
        s.append(vi['sizes'][dim])
    chunks = [1, int(nc2.dim('particle_dim') / 10)] + s
    nc2.create_variable(name, ['time_dim', 'particle_dim'] + dims,
                        vi['dtype'], attributes= vi['attrs'],
                        fill_value= vi['attrs']['_FillValue'],
                        chunksizes=chunks)
    buffer = np.full([nc2.dim('particle_dim'), ] + [vi['sizes'][dim] for dim in dims],
                     vi['attrs']['_FillValue'], dtype=vi['dtype'])
    for nt, ntr in  enumerate(time_step_range):
        sel = np.arange(ntr[0], ntr[1])
        pID = particleID[sel]  # ID's at this time step
        c = nc1.read_variable(name, sel)
        offsets = pID - ID[0]
        buffer[:] = vi['attrs']['_FillValue']
        buffer[offsets, ...] = c[:]

        # reduce file size  by taking advantage of chunking to only write good values
        n1, n2 = offsets[0], offsets[-1] + 1 # file row offsets
        nc2.file_handle[name][nt, n1:n2, ...] = buffer[n1:n2, ...]

def _write_non_time_depend_part_prop(name,nc1,nc2,ID):

    vi = nc1.variable_info[name]
    dims=[]
    for dim in vi['dims'][1:]:
        nc2.create_dimension(dim, vi['sizes'][dim])
        dims.append(dim)

    nc2.create_variable(name, ['particle_dim'] + dims,
                        vi['dtype'], attributes= vi['attrs'], fill_value= vi['attrs']['_FillValue']
                        )
    buffer = np.full([nc2.dim('particle_dim'), ] + [vi['sizes'][dim] for dim in dims],
                     vi['attrs']['_FillValue'], dtype=vi['dtype'])
    offsets = ID - ID[0]
    c = nc1.read_variable(name)
    buffer[offsets, ...] = c[:]
    nc2.file_handle[name][:] = buffer



if __name__ == "__main__":
    if True:
        fnbase=r'C:\Auck_work\oceantracker_output\unit_test_reference_cases\unit_test_18_rectangular_compact_tracks_00\unit_test_18_rectangular_compact_tracks_00_tracks_compact_00**.nc'
        r= range(0,4)
    else:
        fnbase = r'C:\Auck_work\oceantracker_output\unit_tests\unit_test_80_LagrangianStructuresFTLE_00_demoSchism3D\unit_test_80_LagrangianStructuresFTLE_00_demoSchism3D_tracks_compact_00**.nc'
        r = range(0,1)

    t0 = perf_counter()
    for n in r:
        fn1 = fnbase.replace('**',str(n))
        print(path.basename(fn1))
        fn2 = convert_compact_file(fn1)
        print(fn2)

    print('Conversion time', perf_counter()-t0)

    check1= read_ncdf_output_files.read_tracks_file(fn1)
    check2= read_ncdf_output_files.read_tracks_file(fn2)
    dx =  check2['x'] - check1['x']

    print('check compact and retangular conversionare the same')
    print('x diffs min/mean,max.',np.nanmin(np.nanmin(dx,axis=0),axis=0),
            np.nanmean(np.nanmean(dx, axis=0), axis=0),np.nanmax(np.nanmax(dx,axis=0),axis=0))





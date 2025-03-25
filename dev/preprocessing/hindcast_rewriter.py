# class to rewrite hindcast by splting fins, and/or scale and offset compressions

from glob import glob
import xarray as xr
import numpy as np
from os import path, mkdir

class RewriteHindcast():
    def __init__(self,input_dir, file_mask, test=True):

        self.input_dir=input_dir
        self. file_mask=file_mask
        self.var_encoding = dict()

        glob_mask = path.join(input_dir, '**',file_mask)

        self.file_list=  glob(glob_mask, recursive=True)
        if test:
            self.file_list = [self.file_list[0]]


    def show_vars(self):
        ds =  xr.open_dataset(self.file_list[0])
        for name, v in ds.variables.items():
            min, max = np.nanmin(v),np.nanmax(v)
            print(f'{name:15}  dtype= {v.dtype}, dims={v.dims},  shape={v.shape}', 'min=',min, 'max=', max )
        pass
    def encode_var(self,name, min_max=None, compression=0):

        self.var_encoding[name] = dict(min_max=min_max,compression=compression)
        pass

    def write(self,output_dir,dropvars=[]):

        ve = self.var_encoding
        self.file_list_out=[]

        if not path.isdir(output_dir):
            mkdir(output_dir)

        for fn in self.file_list:
            dataset = xr.open_dataset(fn)
            output_dataset = dataset.copy()
            endcoding=dict()

            for name, v in output_dataset.variables.items():
                if name in dropvars: continue
                if name in ve:
                    min_max= ve[name]['min_max']
                    if min_max is not None:
                        endcoding[name] =self._compute_scale_and_offset( min_max, n=16) # as int16
                        endcoding[name].update(dict(dtype=np.int16, _FillValue=np.iinfo(np.int16).min))
                        v = v.where(v < min_max[0], endcoding[name]['_FillValue'])
                        v = v.where(v > min_max[1], endcoding[name]['_FillValue'])

                    if ve[name]['compression'] > 0:
                        endcoding[name].update(dict(zlib=True, complevel=ve[name]['compression']))

            base = fn.split(self.input_dir)[-1]

            fn_output = output_dir +base
            print('writing', fn_output)
            self.file_list_out.append(fn_output)
            output_dataset.to_netcdf(fn_output,encoding=endcoding)

        self.compare_compressed_file()


    def compare_compressed_file(self):
        d_in = xr.open_dataset(self.file_list[0])
        d_out = xr.open_dataset(self.file_list_out[0])

        for name, v in d_out.variables.items():
            if 'scale_factor' in v.encoding:
                print(name,'compare, max diff', np.nanmax( (d_out[name] - d_in[name]).compute()))
                pass
        pass



    def _compute_scale_and_offset(self, min_max, n=16):
        min, max = min_max
        min, max = float(min), float(max)
        # stretch/compress data to the available packed range
        scale_factor = (max - min) / (2 ** n - 1)
        # translate the range to be symmetric about zero
        add_offset = min + 2 ** (n - 1) * scale_factor
        return  dict(scale_factor= scale_factor, add_offset=add_offset)


if __name__ == "__main__":

    input_dir=r'D:\Hindcast_reader_tests\Delft3D\Stantech_hananui_delft3DFM_version1'
    file_mask = r'han*.nc'
    output_dir = r'D:\Hindcast_reader_tests\Delft3D\Stantech_hananui_delft3DFM_version1_compressed'

    h= RewriteHindcast(input_dir, file_mask, test=True)
    h.show_vars()
    compress=0
    for name in ['mesh2d_u1', 'mesh2d_ucx','mesh2d_ucy','mesh2d_ucxa','mesh2d_ucya','mesh2d_ucmag','mesh2d_ucmaga']:
        h.encode_var(name, min_max=[-10,10],compression=compress)

    h.encode_var('mesh2d_s1', min_max=[-10, 10], compression=compress)
    h.encode_var('mesh2d_waterdepth', min_max=[-10, 600],compression=compress)

    h.encode_var('mesh2d_ucz', min_max=[-1, 1],compression=compress)
    h.encode_var('mesh2d_ww1', min_max=[-1, 1],compression=compress)
    h.encode_var('mesh2d_TidalPotential', min_max=[-5, 5], compression=compress)

    for name in ['mesh2d_windx', 'mesh2d_windy', 'mesh2d_windxu', 'mesh2d_windyu']:
        h.encode_var(name, min_max=[-20, 20],compression=compress)

    h.write(output_dir)


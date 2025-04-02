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
        self.max = dict(wind_speed=100, hori_vel=10, vert_vel=1., tide=10)
        self.variables_to_add = dict()

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

    def write(self,output_dir, time_variable, dropvars=[], file_base=None, time_steps_per_file=None):

        self.file_list_out=[]

        if not path.isdir(output_dir):
            mkdir(output_dir)

        for fn in self.file_list:
            dataset = xr.open_dataset(fn)

            time_dim = dataset[time_variable].dims[0]
            time_steps = dataset[time_variable].size
            time_steps_per_file = time_steps if time_steps_per_file is None else time_steps_per_file

            for sel_time_steps in np.array_split(np.arange(time_steps), int(time_steps/time_steps_per_file)):
                self._write_a_file(fn, dataset, time_variable,time_dim,  dropvars, sel_time_steps,splitting_file=sel_time_steps.size < time_steps)

        self.compare_compressed_file()

    def _write_a_file(self,source_file_name,dataset,  time_variable,time_dim,  dropvars, sel_time_steps, splitting_file):

        output_dataset = xr.Dataset()
        output_dataset.attrs = dataset.attrs

        ve = self.var_encoding
        endcoding = dict()

        for name, v in dataset.variables.items():
            if name in dropvars: continue


            if time_dim in v.dims:
                # select times
                data = v.isel(time=sel_time_steps)
            else:
                data = v

            if name in ve:
                min_max = ve[name]['min_max']
                if min_max is not None:
                    data, sf =  self._compute_scale_and_offset(data, min_max)  # as int16
                    data.attrs.update(sf)
                    endcoding[name] ={}
                    #endcoding[name].update(dict(dtype=np.int16, _FillValue=np.iinfo(np.int16).min))


                if ve[name]['compression'] > 0:
                    endcoding[name].update(dict(zlib=True, complevel=ve[name]['compression']))
            output_dataset[name] = data

        base = source_file_name.split(self.input_dir)[-1]
        base, ext = path.splitext(base)
        out_file_name = path.basename(base)
        if splitting_file:
            # splitting file
            base = f'{base}_{str(output_dataset[time_variable].data[0]).split(".")[0]}'.replace(':','_')

        fn_output = output_dir + base + ext
        print('writing', fn_output)
        self.file_list_out.append(fn_output)
        output_dataset.to_netcdf(fn_output, encoding=endcoding)
        pass

    def compare_compressed_file(self):
        d_in = xr.open_dataset(self.file_list[0])

        d_out = xr.open_dataset(self.file_list_out[0])
        d_in = d_in.sel(time=d_out['time'])

        for name, v in d_out.variables.items():
            if 'scale_factor' in v.encoding:
                print(name,'compare, max diff', np.nanmax( (d_out[name] - d_in[name]).compute()))
                pass
        pass

    def add_variable(self, name, data, dims):
          self.variables_to_add[name] = xr.DataArray(name, data, dims=dims)

    def _compute_scale_and_offset(self,data,  min_max):
        # convert float to scaled and offset int32

        min, max = min_max
        min, max = float(min), float(max)

        i32 = np.iinfo(np.int16)
        e=dict(_FillValue=i32.min )
        data = data.where(data >= min_max[0], other = e['_FillValue'])
        data = data.where(data <= min_max[1], other=e['_FillValue'])
        sel = np.any(data==e['_FillValue'])

        data = data.where( ~np.isnan(data), other= e['_FillValue'])

        # stretch/compress data to the available packed range
        # n=16
        #e['scale_factor'] = (max - min) / (2 ** n - 1)
        e['scale_factor'] = (max - min) / (i32.max-(i32.min +1)) # reserve -32768 for missing value


        # translate the range to be symmetric about zero
        #e['add_offset'] =  min + 2 ** (n - 1) * e['scale_factor']
        e['add_offset'] = min + i32.max * e['scale_factor']

        # ( np.asarray(min_max) -  e['add_offset'] )/e['scale_factor'] # check  of min_max maps to [-32767.,  32767.], leaving  -32768 for missing value

        data = (data -  e['add_offset'] )/e['scale_factor']
        data = data.astype(np.int32)
        return data,  e


    def DEFT3D_var_encoding(self,max_depth, compress = 0):
        # add encoding to common variables
        # hori velocity
        for name in ['mesh2d_u1', 'mesh2d_ucx', 'mesh2d_ucy', 'mesh2d_ucxa', 'mesh2d_ucya', 'mesh2d_ucmag', 'mesh2d_ucmaga']:
            self.encode_var(name, min_max=[-self.max['hori_vel'], self.max['hori_vel']], compression=compress)

        self.encode_var('mesh2d_s1', min_max=[-self.max['tide'], self.max['tide']], compression=compress) # tide

        # tides
        self.encode_var('mesh2d_waterdepth', min_max=[-10, max_depth], compression=compress)
        self.encode_var('mesh2d_TidalPotential', min_max=[-self.max['tide'], self.max['tide']], compression=compress)

        # vertical vel
        self.encode_var('mesh2d_ucz', min_max=[-self.max['vert_vel'], self.max['vert_vel']], compression=compress)
        self.encode_var('mesh2d_ww1', min_max=[-self.max['vert_vel'], self.max['vert_vel']], compression=compress)

        # wind speeds
        for name in ['mesh2d_windx', 'mesh2d_windy', 'mesh2d_windxu', 'mesh2d_windyu']:
            self.encode_var(name, min_max=[-self.max['wind_speed'], self.max['wind_speed']], compression=compress)

if __name__ == "__main__":

    ncase = 0
    match ncase:
         case 0:
            input_dir=r'D:\Hindcast_reader_tests\Delft3D\Stantech_hananui_delft3DFM_version1'
            file_mask = r'han*.nc'
            output_dir = r'D:\Hindcast_reader_tests\Delft3D\Stantech_hananui_delft3DFM_version1_compressed'

            h= RewriteHindcast(input_dir, file_mask, test=True)
            h.show_vars()

            h.DEFT3D_var_encoding(600, compress=0)
            s = np.linspace(0,1,11)
            h.add_variable('mesh2d_interface_sigma' , s,['s'] )

            h.write(output_dir,'time',time_steps_per_file=12)


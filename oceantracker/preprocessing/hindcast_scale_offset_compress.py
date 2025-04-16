# class to rewrite hindcast by splting fins, and/or scale and offset compressions

from glob import glob
import xarray as xr
import numpy as np
from os import path, mkdir

class RewriteHindcast():
    def __init__(self,input_dir, file_mask, test=True):

        self.input_dir = input_dir
        self.file_mask=file_mask
        self.var_encoding = dict()
        self.max = dict(wind_speed=100, hori_vel=10, vert_vel=1., tide=10)
        self.variables_to_add = dict()
        self.file_info =dict()

        glob_mask = path.join(input_dir, '**',file_mask)

        self.file_list=  glob(glob_mask, recursive=True)
        self.test = test

        if len(self.file_list) ==0:
            raise FileNotFoundError( f'no files found with, "{input_dir}", "{file_mask}"')
        if test:
            self.file_list = [self.file_list[0]]




    def show_var_min_max(self):
        ds =  xr.open_dataset(self.file_list[0])
        print('_________ variable info______first 100 time steps from first file________________________________')
        time_dim = self.file_info['time_dim']
        n = min(ds.dims[time_dim],100)
        for name, v in ds.variables.items():
            if time_dim in v.dims:
                v_part =  v.isel( {self.file_info['time_dim'] : np.arange(n)})
            else:
                v_part = v
            data_min, data_max = np.nanmin(v_part),np.nanmax(v_part)
            print(f'{name:15}  dtype= {v.dtype}, dims={v.dims},  shape={v.shape}', 'min=',data_min, 'max=', data_max)
            print ('\t \t  attrib=', str(v.attrs) )
        pass
    def encode_var(self,name, min_max=None,use_data_limits=False):
        self.var_encoding[name] = dict(min_max=min_max,use_data_limits=use_data_limits)
        pass

    def write(self,output_dir, dropvars=[], time_steps_per_file=None,
              compression=0,start=None, end=None):
        print('------------Start compression -------------')
        self.file_list_out=[]

        if not path.isdir(output_dir):
            mkdir(output_dir)

        for fn in self.file_list:
            dataset = xr.open_dataset(fn)
            time_variable = self.file_info['time_variable']
            time_steps = dataset[time_variable].size
            time_steps_per_file = time_steps if time_steps_per_file is None else time_steps_per_file

            print('compressing ', fn, str(dataset[time_variable][0].data))


            for n, sel_time_steps in enumerate(np.array_split(np.arange(time_steps), int(time_steps/time_steps_per_file))):
                if self.test and n >= 7:continue # only write 3 files
                self._write_a_file(fn, dataset,  dropvars, sel_time_steps, compression,
                                   splitting_file=sel_time_steps.size < time_steps,
                                   start= start, end = end)

        self.compare_compressed_file()

    def _write_a_file(self,source_file_name,dataset, dropvars, sel_time_steps,compression,
                      splitting_file, start, end):
        time_variable = self.file_info['time_variable']
        time_dim = self.file_info['time_dim']

        output_dataset = xr.Dataset()
        output_dataset.attrs = dataset.attrs
        # add user added variables
        for name, var in self.variables_to_add.items():
            output_dataset[name] = var

        ve = self.var_encoding
        endcoding = dict()

        for name, v in dataset.variables.items():
            if name in dropvars: continue

            if time_dim in v.dims:
                # select times
                data = v.isel({time_dim: sel_time_steps})
            else:
                data = v
            data.attrs.update(v.attrs)


            if name in ve:
                if ve[name]['use_data_limits']:
                    data_min, data_max = np.nanmin(data), np.nanmax(data)
                    ve[name]['min_max'] = [data_min , data_max ]

                min_max = ve[name]['min_max']

                if min_max is not None:
                    data, sf =  self._compute_scale_and_offset(data, min_max)  # as int16
                    data.attrs.update(sf)
                    endcoding[name] ={}
                    #endcoding[name].update(dict(dtype=np.int16, _FillValue=np.iinfo(np.int16).min))

                if compression > 0:
                    endcoding[name].update(dict(zlib=True, complevel=compression))
            output_dataset[name] = data

        # trim to start and end
        if start is not None:
            output_dataset = output_dataset.sel( {time_dim : output_dataset[time_variable] >= np.datetime64(start)})
        if end is not None:
            output_dataset = output_dataset.sel({time_dim: output_dataset[time_variable] <= np.datetime64(end)})

        base = source_file_name.split(self.input_dir)[-1]
        base, ext = path.splitext(base)

        if splitting_file:
            # splitting file
            base = f'{base}_{str(output_dataset[time_variable].data[0]).split(".")[0]}'.replace(':','_')

        fn_output = output_dir + base + ext

        self.file_list_out.append(fn_output)
        output_dataset.to_netcdf(fn_output, encoding=endcoding)
        print('\t written ', path.basename(fn_output), '\t start time=', str(output_dataset[time_variable][0].data))
        pass

    def compare_compressed_file(self):
        fn_in = self.file_list[0]
        fn_out = self.file_list_out[0]

        if False:
            #checking as netcdf
            from oceantracker.util.ncdf_util import NetCDFhandler
            n1 = NetCDFhandler(fn_in)
            n2 = NetCDFhandler(fn_out)

        d_in = xr.open_dataset(fn_in)
        d_out = xr.open_dataset(fn_out)
        d_in = d_in.sel({self.file_info['time_dim']: d_out[self.file_info['time_variable']]},  )
        print('')
        print('_____________check  max differences between raw and compressed__ first file only _________________________________')
        warnings={}
        for name, v in d_out.variables.items():
            if 'scale_factor' in v.encoding:
                delta = np.nanmax( (d_out[name] - d_in[name]).compute())
                data_min, data_max = np.nanmin( d_in[name]),np.nanmax( d_in[name])
                p = delta/( data_max -data_min)

                print(name,'\t  max diff=',f'{100*p:5.3f}%', 'or ', delta ,  '\t , range used =', self.var_encoding[name]['min_max'],'data min=', data_min,' max=', data_max)
                if p > 0.001: print('\t Warning, max diff more than 0.1% for ', name)
                pass
        pass

        print('output in  >> ', path.dirname(fn_out))

    def add_variable(self, name, data, dims):
          self.variables_to_add[name] = xr.DataArray(data, dims=dims)

    def _compute_scale_and_offset(self,data,  min_max):
        # convert float to scaled and offset int32

        data_min, data_max = min_max
        data_min, data_max = float(data_min), float(data_max)

        i16= np.iinfo(np.int16)
        e=dict(_FillValue=i16.min )
        data = data.where(data >= min_max[0], other = e['_FillValue'])
        data = data.where(data <= min_max[1], other=e['_FillValue'])
        sel = np.any(data==e['_FillValue'])

        data = data.where( ~np.isnan(data), other= e['_FillValue'])

        # stretch/compress data to the available packed range
         # reserve -32768 for missing value, min max = -32767,32767
        e['scale_factor'] = (data_max - data_min) / (i16.max-i16.min -1) # reserve -32768 for missing value


        # translate the range to be symmetric about zero
        e['add_offset'] = data_min + i16.max * e['scale_factor']

        # ( np.asarray(min_max) -  e['add_offset'] )/e['scale_factor'] # check  of min_max maps to [-32767.,  32767.], leaving  -32768 for missing value

        data = (data -  e['add_offset'] )/e['scale_factor']
        data = data.astype(np.int16)
        return data,  e


    def DEFT3D_encoding(self,scale =True):
        # add encoding to common variables
        # do not scale encode depth
        self.file_info['time_variable'] = 'time'
        self.file_info['time_dim'] = 'time'

        if not scale: return

        # hori vel
        for name in ['mesh2d_u1', 'mesh2d_ucx', 'mesh2d_ucy', 'mesh2d_ucxa', 'mesh2d_ucya', 'mesh2d_ucmag', 'mesh2d_ucmaga']:
            self.encode_var(name, min_max=[-self.max['hori_vel'], self.max['hori_vel']] )

        # vertical vel
        self.encode_var('mesh2d_ucz', min_max=[-self.max['vert_vel'], self.max['vert_vel']] )
        self.encode_var('mesh2d_ww1', min_max=[-self.max['vert_vel'], self.max['vert_vel']] )

        self.encode_var('mesh2d_s1', min_max=[-self.max['tide'], self.max['tide']]) # tide

        # tides
        self.encode_var('mesh2d_TidalPotential', min_max=[-self.max['tide'], self.max['tide']])


        # wind speeds
        for name in ['mesh2d_windx', 'mesh2d_windy', 'mesh2d_windxu', 'mesh2d_windyu']:
            self.encode_var(name, min_max=[-self.max['wind_speed'], self.max['wind_speed']])

        self.encode_var('mesh2d_Patm', min_max=[50000,150000])

    def SCHISM_encoding(self, scale=True):
        # add encoding to common variables for original schism format
        # do not scale encode depth
        self.file_info['time_variable'] = 'time'
        self.file_info['time_dim'] = 'time'

        if not scale: return

        # hori vel
        for name in ['dahv', 'hvel']:
            self.encode_var(name, min_max=[-self.max['hori_vel'], self.max['hori_vel']])
        # vertical vel
        self.encode_var('vertical_velocity', min_max=[-self.max['vert_vel'], self.max['vert_vel']])


        self.encode_var('temp', min_max=[-10, 50])
        self.encode_var('salt', min_max=[-1, 100])

        for name in ['zcor', 'TKE', 'wind_stress','diffusivity','viscosity','mixing_length']:
            self.encode_var(name, use_data_limits=True)

        # tides
        self.encode_var('elev', min_max=[-self.max['tide'], self.max['tide']] )


        # wind speeds
        for name in ['wind_speed']:
            self.encode_var(name, min_max=[-self.max['wind_speed'], self.max['wind_speed']] )

        self.encode_var('mesh2d_Patm', min_max=[50000,150000])

    def ROMS_encoding(self, scale=True):
        # add encoding to common variables for original schism format
        # do not scale encode depth
        self.file_info['time_variable'] = 'ocean_time'
        self.file_info['time_dim'] = 'ocean_time'

        if not scale: return

        # hori vel
        for name in ['u', 'v','ubar','vbar','u_eastward','v_northward']:
            self.encode_var(name, min_max=[-self.max['hori_vel'], self.max['hori_vel']])

        # vertical vel
        self.encode_var('w', min_max=[-self.max['vert_vel'], self.max['vert_vel']])

        self.encode_var('temp', min_max=[-10, 50])
        self.encode_var('salt', min_max=[-1, 100])

        for name in ['shflux','ssflux','AKs','AKt','AKv','swrad_daily','sustr','sustr',
                     'DU_avg1','DU_avg2','DV_avg1','DV_avg2',]:
            self.encode_var(name, use_data_limits=True)

        # tides
        self.encode_var('elev', min_max=[-self.max['tide'], self.max['tide']] )
        self.encode_var('zeta', min_max=[-self.max['tide'], self.max['tide']]) # moana tides

        # wind speeds
        for name in ['wind_speed']:
            self.encode_var(name, min_max=[-self.max['wind_speed'], self.max['wind_speed']] )

        self.encode_var('mesh2d_Patm', min_max=[50000,150000])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-test_mode', action='store_true')
    parser.add_argument('--example', type=int, default=1)
    args = parser.parse_args()

    match args.example:
        case 1:
            input_dir=r'D:\Hindcast_reader_tests\Delft3D\Stantech_hananui_delft3DFM_test1'
            file_mask = r'R3_*.nc'
            output_dir = r'D:\Hindcast_reader_tests\Delft3D\Stantech_hananui_delft3DFM_test1\compressed_version1'

            h= RewriteHindcast(input_dir, file_mask, test=args.test_mode)
            h.DEFT3D_encoding(scale =True)

            # use h.encode_var() to override any min,maxs sset in above
            h.show_var_min_max()  # show mins and max, dims  for all variables in first file, must be after encoding cll

            s = -np.arange(0,1.1,.1)[::-1]
            h.add_variable('mesh2d_interface_sigma' , s, ['mesh2d_nInterfaces'])
            h.add_variable('mesh2d_layer_sigma', (.05+s[:-1]), ['mesh2d_nLayers'])
            h.write(output_dir,time_steps_per_file=24,start ='2018-06-01T00:00:00.000000000')

        case 2:
            input_dir = r'D:\Hindcast_reader_tests\Schisim\Auckland_uni_hauraki\original'
            file_mask = r'sc*.nc'
            output_dir = r'D:\Hindcast_reader_tests\Schisim\Auckland_uni_hauraki\compressed'

            h = RewriteHindcast(input_dir, file_mask, test=args.test_mode)
            h.SCHISM_encoding(scale =True)

            # use h.encode_var() to override any min,maxs sset in above
            h.show_var_min_max()  # show mins and max, dims  for all variables in first file, must be after encoding cll

            h.write(output_dir, compression=5)
        case 3:
            input_dir = r'D:\Hindcast_reader_tests\ROMS_samples\ROMS_Mid_Atlantic_Bight\original'
            file_mask = r'doppio_his*.nc'
            output_dir = r'D:\Hindcast_reader_tests\ROMS_samples\ROMS_Mid_Atlantic_Bight\compressed'

            h = RewriteHindcast(input_dir, file_mask, test=args.test_mode)
            h.ROMS_encoding(scale=True)

            # use h.encode_var() to override any min,maxs sset in above
            h.show_var_min_max()  # show mins and max, dims  for all variables in first file, must be after encoding cll

            h.write(output_dir, compression=5)

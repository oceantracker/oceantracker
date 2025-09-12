from netCDF4 import Dataset
from oceantracker.util import numpy_util

import numpy as np
from os import path
from copy import  deepcopy
class NetCDFhandler(object):
    # wrapper for single necdf cdf file, to do common operations
    # allows for only one unlimited dimension so far
    def __init__(self, file_name, mode='r'):

        # get a file handle
        self.file_name = file_name

        self.mode = mode

        path.isfile(file_name)
        try:
            self.file_handle = Dataset(self.file_name, mode)
        except Exception as e:
            print('Ocean tracker could not create/find/read netCDF file="' + file_name + '"' + ', mode =' + mode)
            raise(e)
        except PermissionError as e:
            print('Ocean tracker does not have permission to create netCDF file="' + file_name + '"' + ', mode =' + mode +' try deleting file')
            raise (e)

        self.max_bytes_per_chunk= 4*10**9 # looks like chunks cant exceeded 4gb each

        self.variable_info ={}
        if mode == 'r':
            # get variable info
            v = self.file_handle.variables
            for name in v.keys():
                self.variable_info[name] ={'dims':v[name].dimensions,
                       'shape': v[name].shape,'dtype': v[name].datatype,
                       'attrs': self.var_attrs(name),
                       'sizes': {name: s for name,s in zip(v[name].dimensions, v[name].shape) }
                        }

    def create_dimension(self, name, dim_size=None):
        # add a dimension for use in netcdf
        # print('AD',name,dim_size)
        if name not in self.file_handle.dimensions:
            self.file_handle.createDimension(name, dim_size)

    def create_variable(self, name, dimList, dtype, description=None, fill_value=None, units=None,
                        attributes=None, chunksizes=None, compression_level=0):
        # add and write a variable of given nane and dim name list
        if type(dimList) ==str: dimList=[dimList]
        dimList = list(dimList)
        attributes = deepcopy(attributes)
        dtype = np.dtype(dtype) # convert string dtypes
        if attributes is not None and '_FillValue' in attributes:
            if fill_value is None: fill_value =attributes['_FillValue']
            del attributes['_FillValue']

        if fill_value is None:  fill_value = numpy_util.smallest_value(dtype)

        v = self.file_handle.createVariable(name, dtype, tuple(dimList), chunksizes=chunksizes, zlib=(compression_level > 0),
                            complevel=compression_level, fill_value=fill_value)

        # set attributes the hard way, must be an easier way!
        if description is not None:
            setattr(self.file_handle.variables[name], 'description', self._sanitize_attribute(description))
        if units is not None:
            setattr(self.file_handle.variables[name], 'units', self._sanitize_attribute(units))

        if attributes is not None:
            for key, value in attributes.items():
                setattr(self.file_handle.variables[name], key, self._sanitize_attribute(value))
        return v

    def read_variable(self, name, sel=None):
        # read a variable or sel of first dimension
        if sel is None:
            data= self.file_handle.variables[name][:]   # read whole variable
        else:
            data = self.file_handle.variables[name][sel, ...] # selection from first dimension

        out = np.asarray((data))

        return out

    def read_variables(self, var_list=None, required_var=[], output=None, sel=None):
        # read a list of variables into a dictionary, if output is a dictionary its add to that one
        # sel is which values to read from first dimension
        if output is None:  output=dict(variable_attributes=dict())
        if var_list is None:  var_list = self.var_names()

        name_list = list(set(var_list + required_var))
        for name in name_list:
            output[name] = self.read_variable(name, sel=sel)
            output['variable_attributes'][name] = self.var_attrs(name)
        output['global_attributes'] = self.attrs()
        return output

    def write_variable(self, name, data, dimList, description=None,
                       attributes={}, dtype=None, chunksizes=None, units=None,
                       compression_level=0,
                       fill_value= None):
        # write a whole variable and add dimensions if required
        if type(dimList) != list and type(dimList) != tuple :dimList =[dimList]

        if data.ndim != len(dimList):
            raise Exception('write_a_new_variable: NCDF variable = ' + name + ' must have same number of dimensions as length of dimList' )

        # cycle through dims list to add dimension, if needed
        for n in range(len(dimList)):
            self.create_dimension(dimList[n], data.shape[n])  # an unlimted dimension

        if dtype is None: dtype = data.dtype  # preserve type unless explicitly changed

        v = self.create_variable(name, dimList, description=description,
                                 attributes= attributes, dtype=dtype, chunksizes= chunksizes,
                                 units= units, compression_level=compression_level, fill_value=fill_value)

        # check dims match as below write does not respect shape
        for n,dn in enumerate(dimList):
            if self.dim(dn) != v.shape[n]:
                raise ValueError('Size of dimension ' + dn + '(=' + str(v.shape[n]) + ')  for   variable ' + name +
                                 ' does not  size of defined dimension ' + dn + '(=' + str(self.dim(dn)) + ')')
        v[:] = data[:]  # write X
        pass

    def create_attribute(self, name, value) : setattr(self.file_handle, name, self._sanitize_attribute(value))

    # dimensions
    def dims(self): return {name: val.size for name, val in self.file_handle.dimensions.items()}

    def dim(self, name): return self.file_handle.dimensions[name].size

    def is_dim(self,dim_name):return dim_name in self.file_handle.dimensions

    def attr(self, name): return getattr(self.file_handle, name)
    def is_attr(self, name):  return name in self.file_handle.__dict__

    def attrs(self):  return self.file_handle.__dict__

    def is_var(self, name):  return name in self.file_handle.variables
    def is_var_dim(self, var_name, dim_name): return dim_name in self.var_dims(var_name)

    def var_attr(self, name, attr_name):  return getattr(self.file_handle.variables[name], attr_name)
    # variables
    def var_attrs(self, var_name): return  self.file_handle[var_name].__dict__# Get all  attributes of the NetCDF file
    def is_var_attr(self, name, attr_name):  return hasattr(self.file_handle.variables[name], attr_name)

    def var_names(self):  return list(self.file_handle.variables.keys())
    def var_dims(self, var):  return list(self.file_handle.variables[var].dimensions)

    def var_shape(self, var):  return self.file_handle.variables[var].shape

    def var_dtype(self,name):
        # to allow for netcd scal and fit of integers
        # get dtype by reading one  value
        dtype = self.file_handle.variables[name][0].dtype
        return dtype

    def var_fill_value(self, name): return self.file_handle.variables[name]._FillValue

    def _sanitize_attribute(self,value):
        if type(value) is  bool: value =int(value) #  convert booleans
        if value       is None : value = 'None'  # convert Nones
        return value

    def copy_global_attributes(self,nc_new):
        for name, val in self.attrs().items():
            nc_new.create_attribute(name, val)

    def copy_variable(self,name, nc_new, compression_level=0):
        v = self.file_handle[name]

        #write_a_new_variable(self, name, X, dimList, description=None, attributes=None, dtype=None, chunksizes=None, compression_level=0):
        attributes = self.var_attrs(name)
        if '_FillValue' in attributes:
            fill_value=attributes['_FillValue' ]
            del attributes['_FillValue']
        else:
            fill_value = None
        nc_new.write_variable(name, v[:], v.dimensions,
                              fill_value=fill_value,
                              attributes=attributes,
                              compression_level=compression_level,
                              )
        pass

    def write_packed_1Darrays(self, name, array_list, description=None, attributes=None, dtype=None, chunksizes=None,
                              compression_level=0, fill_value=None, units=None):
        # write list of numpy 1D arrays  which differ in size,
        # as a single array with unpacking data, m

        out = np.full((0,),-1,dtype=array_list[0].dtype)
        ranges = np.full((0,2),-1,dtype=np.int32)
        n_start = 0
        for  a in array_list:
            m = a.shape[0]
            ranges = np.concatenate((ranges, np.asarray([n_start, n_start+m]).reshape(1,2)), axis=0)
            out =np.concatenate((out, a),axis=0)
            n_start += m

        pass
        ranges_var= f'{name}_packed_ranges'
        self.write_variable(name, out, f'{name}_packed_dim',
                            description= description+' packed array',
                            attributes=dict(ranges_var =ranges_var)
                            )
        self.write_variable(ranges_var, ranges, [f'{name}_ranges_dim', 'range_pair_dim'],
                            description=description + ' packed array',
                            attributes=dict(ranges_var=ranges_var)
                            )
        pass

    def un_packed_1Darrays(self, name:str):
        '''  unpack variable of given name, from range variable '''
        out =[]
        data =  self.read_variable(name)
        ranges = self.read_variable(self.var_attr(name, 'ranges_var'))
        for r in ranges:
            out.append(data[r[0]:r[1]])
        return out

    def close(self):
        self.file_handle.close()
        self.file_handle = None  # parallel pool cant pickle nc so void

def compute_scale_and_offset_int16(data, missing_value=None):
    # scale data into int32's
    # mask and get min
    if missing_value is not None:
        data[data == missing_value] = np.nan
    dmin, dmax = np.nanmin(data), np.nanmax(data)

    # int 16 negative 32768 through positive 32767
    # stretch/compress data to the available packed range
    i16 =np.iinfo(np.int16)

    i16_range = float(i16.max - 2)  # range with last value reserved for missing value

    # translate the range to be symmetric about zero
    add_offset   = (dmin+.5*(dmax-dmin)).astype(data.dtype)
    scale_factor = ((dmax - add_offset)/i16_range).astype(data.dtype)

    # mask with new missing value
    missing_value = -i16.max
    #data[np.isnan(data)] = missing_value
    #data = np.round(data,0).astype(np.int16)
    print('\t scaled',dmin, dmax , scale_factor, add_offset, missing_value)

    return data, scale_factor, add_offset, missing_value

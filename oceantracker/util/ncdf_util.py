from netCDF4 import Dataset


import numpy as np
from os import path

class NetCDFhandler(object):
    # wrapper for single necdf cdf file, to do common operations
    # allows for only one unlimited dimension so far
    def __init__(self, file_name, mode='r'):

        # get a file handle
        self.file_name = file_name
        self.mode = mode
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
                    self.variable_info[name] ={'dimensions':v[name].dimensions,
                                               'shape': v[name].shape,'dtype': v[name].datatype,
                                               'attributes': self.all_var_attr(name)}


    def add_dimension(self, name, dim_size=None):
        # add a dimension for use in netcdf
        # print('AD',name,dim_size)
        if name not in self.file_handle.dimensions:
            self.file_handle.createDimension(name, dim_size)

    def create_a_variable(self, name, dimList,dtype, description=None, fill_value=None,units=None,
                          attributes=None,  chunksizes=None, compressionLevel=0):
        # add and write a variable of given nane and dim name list
        if type(dimList) != list and type(dimList) != tuple: dimList = [dimList]
        if dtype is None: dtype = np.float64  # double by default
        dtype = np.dtype(dtype) # convert string dtypes
        if fill_value is None:
            if dtype in [np.float64, np.float32]:
                fill_value = np.nan
            elif np.issubclass_(np.int32,np.integer):
                fill_value = -128
            else:
                fill_value = -128

        v = self.file_handle.createVariable(name, dtype, tuple(dimList), chunksizes=chunksizes, zlib=(compressionLevel > 0),
                                                complevel=compressionLevel, fill_value=fill_value)

        # set attributes the hard way, must be an easier way!
        if description is not None:
            setattr(self.file_handle.variables[name], 'description', self._sanitize_attribute(description))
        if units is not None:
            setattr(self.file_handle.variables[name], 'units', self._sanitize_attribute(units))

        if attributes is not None:
            for key, value in attributes.items():
                setattr(self.file_handle.variables[name], key, self._sanitize_attribute(value))
        return v

    def read_a_variable(self,name, sel=None):
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
        if var_list is None:  var_list = self.all_var_names()

        name_list = list(set(var_list+required_var))
        for name in name_list:
            output[name] = self.read_a_variable(name, sel=sel)
            output['variable_attributes'][name] = self.all_var_attr(name)
        output['global_attributes'] = self.global_attrs()
        return output

    def write_a_new_variable(self, name, data, dimList, description=None,
                             attributes={},dtype=None, chunksizes=None,units=None,
                             compressionLevel=0,
                             missing_value= None):
        # write a whole variable and add dimensions if required
        if type(dimList) != list and type(dimList) != tuple :dimList =[dimList]

        if data.ndim != len(dimList):
            raise Exception('write_a_new_variable: NCDF variable = ' + name + ' must have same number of dimensions as length of dimList' )

        # cycle through dims list to add dimension, if needed
        for n in range(len(dimList)):
            self.add_dimension(dimList[n], data.shape[n])  # an unlimted dimension

        if dtype is None: dtype = data.dtype  # preserve type unless explicitly changed

        v = self.create_a_variable(name, dimList,description=description,
                    attributes= attributes,dtype=dtype, chunksizes= chunksizes,
                    units= units,  compressionLevel=compressionLevel, fill_value=missing_value)

        # check dims match as below write does not respect shape
        for n,dn in enumerate(dimList):
            if self.dim_size(dn) != v.shape[n]:
                raise ValueError('Size of dimension ' + dn + '(=' +   str(v.shape[n]) + ')  for   variable ' +  name +
                                 ' does not  size of defined dimension ' + dn + '(=' +   str(self.dim_size(dn)) + ')' )
        v[:] = data[:]  # write X
        pass

    def write_part_of_first_dim_of_variable(self,name,data, sel):
        # write data as part of first dim of named variable with give indicies, only if numpy array list in sel indices is not empty
        if sel.shape[0] > 0:
            self.file_handle.variables[name][sel, ...] = data[:]

    def write_global_attribute(self, name,value) :
        setattr(self.file_handle, name, self._sanitize_attribute(value))
        pass
    # get data
    # check if variables or list of variables in file
    def is_var(self, name):
        return name in self.file_handle.variables

    def are_vars(self, name_list):
        a = []
        for n in name_list:
            a.append(self.is_var(n))
        return a

    def are_all_vars(self, name_list):  return all(self.are_vars(name_list))

    # dimensions
    def dim_list(self): return list(self.file_handle.dimensions.keys())

    def dims(self):
        out= {}
        for dim_name, val in  self.file_handle.dimensions.items():
            out[dim_name] =  self.file_handle.dimensions[dim_name].size
        return out

    def dim_size(self,dim_name):  return self.file_handle.dimensions[dim_name].size

    def is_dim(self,dim_name):return dim_name in self.file_handle.dimensions

    def global_attr_names(self): return  self.file_handle.ncattrs()
    def global_attr(self, attr_name): return getattr(self.file_handle, attr_name)
    def global_attrs(self):  return self.file_handle.__dict__

    # variables
    def all_var_attr(self,var_name): return  self.file_handle[var_name].__dict__# Get all  attributes of the NetCDF file
    def is_var_attr(self, name, attr_name):  return hasattr(self.file_handle.variables[name], attr_name)

    def var_data(self, name):   return self.file_handle.variables[name][:]

    def all_var_names(self):
        return list(self.file_handle.variables.keys())
    def all_var_dims(self,var):
        return list(self.file_handle.variables[var].dimensions)

    def var_shape(self, var):  return self.file_handle.variables[var].shape
    def var_fill_value(self,var_name): return

    def var_attr(self, name, attr_name):
        return getattr(self.file_handle.variables[name], attr_name)

    def var_dtype(self,name):
        # to allow for netcd scaland fit of integers
        # get dtype by reading one  vaule
        dtype = self.file_handle.variables[name][0].dtype
        return dtype

    def var_fill_value(self, name):
        return self.file_handle.variables[name]._FillValue

    def is_var_dim(self, var_name, dim_name):
        return dim_name in self.all_var_dims(var_name)

    def get_fh(self): return self.file_handle

    def _sanitize_attribute(self,value):
        if type(value) is  bool: value =int(value) #  convert booleans
        if value       is None : value = 'None'  # convert Nones
        return value

    def copy_global_attributes(self,nc_new):
        for name in self.global_attr_names():
            nc_new.write_global_attribute(name, self.global_attr(name))

    def copy_variable(self,name, nc_new, compressionLevel=0,float32asInt16=False):
        v = self.file_handle[name]

        #write_a_new_variable(self, name, X, dimList, description=None, attributes=None, dtype=None, chunksizes=None, compressionLevel=0):
        attributes = self.all_var_attr(name)
        if '_FillValue' in attributes:
            missing_value=attributes['_FillValue' ]
            del attributes['_FillValue']
        else:
            missing_value = None
        nc_new.write_a_new_variable(name,v[:], v.dimensions,
                                    missing_value=missing_value,
                                    attributes=attributes,
                                    compressionLevel=compressionLevel,
                                    float32asInt16=float32asInt16)
        pass

    def write_packed_1Darrays(self, name, array_list, description=None, attributes=None, dtype=None, chunksizes=None,
                              compressionLevel=0, fill_value=None, units=None):
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
        self.write_a_new_variable(name, out,f'{name}_packed_dim',
                                  description= description+' packed array' ,
                                  attributes=dict(ranges_var =ranges_var)
                                  )
        self.write_a_new_variable(ranges_var, ranges, [f'{name}_ranges_dim','range_pair_dim'],
                                  description=description + ' packed array',
                                  attributes=dict(ranges_var=ranges_var)
                                  )
        pass

    def un_packed_1Darrays(self, name:str):
        '''  unpack variable of given name, from range variable '''
        out =[]
        data =  self.read_a_variable(name)
        ranges = self.read_a_variable(self.var_attr(name,'ranges_var'))
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

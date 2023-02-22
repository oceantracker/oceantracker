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
                    self.variable_info[name] ={'dimensions':v[name].dimensions, 'shape': v[name].shape,'dtype': v[name].datatype}


    def add_dimension(self, name, dim_size=None):
        # add a dimension for use in netcdf
        # print('AD',name,dim_size)
        if name not in self.file_handle.dimensions:
            self.file_handle.createDimension(name, dim_size)

    def create_a_variable(self, name, dimList, attributes=None, dtype=None, chunksizes=None, compressionLevel=0):
        # add and write a variable of given nane and dim name list
        if type(dimList) != list and type(dimList) != tuple: dimList = [dimList]
        if dtype is None: dtype = np.float64  # double by default
        fill_value =-127 if dtype in [np.uint8, np.int8,np.int16,np.int32,np.int64] else np.nan


        v = self.file_handle.createVariable(name, dtype, tuple(dimList), chunksizes=chunksizes, zlib=(compressionLevel > 0),
                                                complevel=compressionLevel, fill_value=fill_value)


        # set attributes the hard way, must be easier way!
        if attributes is not None:
            for key, value in attributes.items():
                setattr(self.file_handle.variables[name], key, self._sanitize_attribute(value))
        return v

    def read_a_variable(self,name, sel=None, time_first_dim=True):
        if sel is None:
            data= self.file_handle.variables[name][:]   # read whole variable
        else:
            if time_first_dim:
                data = self.file_handle.variables[name][sel, ...] # selection from first dimension
            else:
                data = self.file_handle.variables[name][..., sel]  # selection from last dimension
        return np.array(data)

    def read_variables(self, name_list,output=None):
        # read a list of variables into a dictionary, if output is a dictioary its add to that one
        if output is None:  output={}
        for name in name_list:
            output[name]=self.read_a_variable(name)
        return output

    def write_a_new_variable(self, name, X, dimList,  attributesDict=None,dtype=None, chunksizes=None, compressionLevel=0):
        # write a whole variable and add dimensions if required
        if type(dimList) != list and type(dimList) != tuple :dimList =[dimList]

        if X.ndim != len(dimList):
            raise Exception('write_a_new_variable: NCDF variable = ' + name + ' must have same number of dimensions as length of dimList' )

        # cycle through dims list to add dimension, if needed
        for n in range(len(dimList)):
            self.add_dimension(dimList[n], X.shape[n])  # an unlimted dimension

        if dtype is None: dtype = X.dtype  # preserve type unless explicitly changed

        v = self.create_a_variable(name, dimList, attributesDict, dtype, chunksizes, compressionLevel)

        # check dims match as below write does not repect shape
        for n,dn in enumerate(dimList):
            if self.get_dim_size(dn) != v.shape[n]:
                raise ValueError('Size of dimension ' + dn + '(=' +   str(v.shape[n]) + ')  for   variable ' +  name +
                                 ' does not  size of defined dimension ' + dn + '(=' +   str(self.get_dim_size(dn)) + ')' )
        v[:] = X[:]  # write X

    def write_part_of_first_dim_of_variable(self,name,data, sel):
        # write data as part of first dim of named variable with give indicies, only if numpy array list in sel indices is not empty
        if sel.shape[0] > 0:
            self.file_handle.variables[name][sel, ...] = data[:]

    def write_global_attribute(self, name,value) :
        setattr(self.file_handle, name, self._sanitize_attribute(value))
        a=1
    # get data
    # check if variables or list of variables in file
    def is_var(self, name):
        return name in self.file_handle.variables

    def are_vars(self, name_list):
        a = []
        for n in name_list:
            a.append(self.is_var(n))
        return a

    def are_all_vars(self, name_list):        return all(self.are_vars(name_list))

    # dimensions
    def get_dims(self): return self.file_handle.dimensions
    def get_dim_size(self,dim_name):  return self.file_handle.dimensions[dim_name].size

    def is_dim(self,dim_name):return dim_name in self.file_handle.dimensions

    def get_global_attr(self, attr_name): return getattr(self.file_handle, attr_name)

    # variables
    def get_var_names(self): return list(self.file_handle.variables.keys())
    def get_var_dims(self,var):  return list(self.file_handle.variables[var].dimensions)

    def get_var_shape(self, var):  return self.file_handle.variables[var].shape

    def is_var_attr(self, name, attr_name):  return hasattr(self.file_handle.variables[name], attr_name)

    def get_var_attr(self, name, attr_name):  return getattr(self.file_handle.variables[name], attr_name)
    def get_var_dtype(self,name):
        # to allow for netcd scaland fit of integers
        # get dtype by reading one  vaule
        dtype = self.file_handle.variables[name][0].dtype
        return dtype

    def get_var_fillValue(self, name):  return self.file_handle.variables[name]._FillValue

    def is_var_dim(self, var_name, dim_name):
        return dim_name in self.get_var_dims(var_name)

    def get_fh(self): return self.file_handle

    def _sanitize_attribute(self,value):
        if type(value) is  bool: value =int(value) #  convert booleans
        if value       is None : value = 'None'  # convert Nones
        return value

    def close(self):
        self.file_handle.close()
        self.file_handle = None  # parallel pool cant pickle nc so void


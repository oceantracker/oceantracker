# Notes on requirements for oceantracker reader

## Required Parmeters

Below ued to ses if variable id time dependent ot 3D
- hindcast input_dir
- hindcast file_mask
- time_dim_name
- z_dim_name


Optional parameters

- time buffer size
- min_water_depth for dry cell calcu;ltion
- time_zone
- EPSG_transform_code
- isodate_of_hindcast_time_zero
- max_numb_files_to_load
- one_based_indices,used  to adjust to pyhton zero based index
- cords_in_lat_long, will convert to UTM

## Required information methods

- is_3D_hydro_model()
- is_3D_var(file_var_name)
- is_vector(file_var_name) is variable a vector eg bottom stress
- time_sorted_file_list() 

## Grid

Required methods

- read_xy(), reads and transforms xy to required projection if required
- read_triangles(), reads or builds triangulation , splits quad cells etc if required
- read_water_depth(), time independent!
- set_up_vertical_grid(), finds sigma fractions to use for vertical grid

Base method set_up_grid() calls teh above, then 

- which cells to split
- adjacency matrix, boundary nodes etc  

Read time dependent grid variables
- read_time()
- read_dry_cell_flag(file_index, buffer_index) time varying cell property, could use tide and water depth, amd min_depth to calculate dry cell, must account for spliting quad cells cells
- read_zlevels()??? if not regridding to fix uniform sigma.
- other non time varying values?


## Fields

Are time varying, so need buffer index to store

### Core fields

Are time varying and have a "read" method

- read_tide(file_index, buffer_index)
- read_water_velocity(file_index, buffer_index)

### Standard named fields
Uses map from interval name to  file var name for standard internal names which are not core fields, but don't need at map as file variable name is known

optional fields users load these with load_standard_fields parameter if they are in the hindcast file, will interp a particle property by defaults

- wind_stress
- water_temperature
- water_salinity
- bottom_stress

### Custom fields

eg concentration fields, loaded using map in parameter custom_fields 

``{ internal name : file_var_name}```

uses base methods set_up_field.  Need to work out how to deal with custom vector fields, eg map to file_var_name and variable list.

### Transform_methods

- field_info(file_var_name), gets info about feild, is3D, time dependent 
- read_nodal_values_as_4D(file_var_name)


## Utilty routones

- conver

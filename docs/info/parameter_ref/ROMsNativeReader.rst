#################
ROMsNativeReader
#################

**Description:** Generic reader, reading netcdf file variables into variables using given name map between internal and file variable names

**class_name:** oceantracker.reader.ROMS_reader.ROMsNativeReader

**File:** oceantracker/reader/ROMS_reader.py

**Inheritance:** _BaseReader> GenericUnstructuredReader> ROMsNativeReader


Parameters:
************

	* ``EPSG_transform_code`` :   ``<class 'int'>``   *<optional>*
		Description: Integer code needed to enable transformation from/to meters to/from lat/lon (see https://epsg.io/ to find EPSG code for hydro-models meters grid)

		- default: ``None``
		- min: ``0``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``cords_in_lat_long`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``dimension_map``: nested parameter dictionary
	* ``field_variables``: nested parameter dictionary
		* ``bottom_stress`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

		* ``salinity`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

		* ``tide`` :   ``<class 'str'>``   *<optional>*
			- default: ``zeta``

		* ``water_depth`` :   ``<class 'str'>``   *<optional>*
			- default: ``h``

		* ``water_temperature`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

		* ``water_velocity``:  *<optional>*
			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['u', 'v', 'w']``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``

		* ``wind_stress`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

	* ``field_variables_to_depth_average``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``

	* ``file_mask`` :   ``<class 'str'>`` **<isrequired>**
		Description: Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern

		- default: ``None``

	* ``grid_file`` :   ``<class 'str'>``   *<optional>*
		Description: File name with hydrodynamic grid data, as path relative to input_dir, default is get grid from first hindasct file

		- default: ``None``

	* ``grid_variables``: nested parameter dictionary
	* ``input_dir`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``

	* ``isodate_of_hindcast_time_zero`` :   ``iso8601date``   *<optional>*
		- default: ``1970-01-01``

	* ``max_numb_files_to_load`` :   ``<class 'int'>``   *<optional>*
		Description: Only read no more than this number of hindcast files, useful when setting up to speed run

		- default: ``10000000``
		- min: ``1``

	* ``one_based_indices``: nested parameter dictionary
	* ``required_file_dimensions``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['s_w', 's_rho', 'eta_u', 'eta_v']``
		- can_be_empty_list: ``True``

	* ``required_file_variables``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['ocean_time', 'mask_psi', 'lat_psi', 'lon_psi', 'h', 'zeta', 'u', 'v']``
		- can_be_empty_list: ``True``

	* ``time_buffer_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``24``
		- min: ``2``

	* ``time_zone`` :   ``<class 'int'>``   *<optional>*
		Description: time zone in hours relative to UTC/GMT , eg NZ standard time is time zone 12

		- default: ``None``
		- min: ``-12``
		- max: ``12``
		- units: ``hours``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


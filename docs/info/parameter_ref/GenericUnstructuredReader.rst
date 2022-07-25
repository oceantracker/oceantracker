##########################
GenericUnstructuredReader
##########################

**Description:** Generic reader, reading netcdf file variables into variables using given name map between internal and file variable names

**Class:** oceantracker.reader.generic_unstructured_reader.GenericUnstructuredReader

**File:** oceantracker/reader/generic_unstructured_reader.py

**Inheritance:** _BaseReader> GenericUnstructuredReader

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``class_name``:  *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``cords_in_lat_long``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``depth_average``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``description``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``dimension_map``: nested parameter dictionary
		* ``node``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``node``

		* ``time``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``time``

		* ``vector2Ddim``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``None``

		* ``vector3Ddim``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``None``

		* ``z``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``None``

	* ``field_variables``: nested parameter dictionary
		* ``tide``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``None``

		* ``water_depth``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``None``

		* ``water_salinity``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``None``

		* ``water_temperature``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``None``

		* ``water_velocity``:  *<optional>*
			- a list containing type:  ``<class 'str'>``
			- default list item: ``None``
			- can_be_empty_list: ``True``
			- fixed_len: ``3``

	* ``field_variables_to_depth_average``:  *<optional>*
		- a list containing type:  ``<class 'str'>``
		- default list item: ``None``
		- can_be_empty_list: ``True``

	* ``file_mask``:**<isrequired>**
		Description: - Mask for file names, eg "scout*.nc", is joined with "input_dir" to give full file names

		- type: ``<class 'str'>``
		- default: ``None``

	* ``grid_variables``: nested parameter dictionary
		* ``bottom_cell_index``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``None``

		* ``time``:**<isrequired>**
			- type: ``<class 'str'>``
			- default: ``time``

		* ``triangles``:**<isrequired>**
			- type: ``<class 'str'>``
			- default: ``None``

		* ``x``:  *<optional>*
			- a list containing type:  ``<class 'str'>``
			- default list item: ``None``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``

		* ``zlevel``:  *<optional>*
			- type: ``<class 'str'>``
			- default: ``None``

	* ``input_dir``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``isodate_of_hindcast_time_zero``:  *<optional>*
		- type: ``iso8601date``
		- default: ``1970-01-01``

	* ``max_numb_files_to_load``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``10000000``
		- min: ``1``

	* ``minimum_total_water_depth``:  *<optional>*
		Description: - Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering

		- type: ``<class 'float'>``
		- default: ``0.25``
		- min: ``0.0``

	* ``name``:  *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- type: ``<class 'str'>``
		- default: ``None``

	* ``search_sub_dirs``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``time_buffer_size``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``48``
		- min: ``2``

	* ``time_zone``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``None``
		- min: ``-12``
		- max: ``23``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


########################
GenericStructuredReader
########################

**Description:** 

**full class_name :** oceantracker.reader.generic_stuctured_reader.GenericStructuredReader

**short class_name:** GenericStructuredReader

to be added

**Inheritance:** > ParameterBaseClass> _BaseReader> _BaseGenericReader> GenericStructuredReader


Parameters:
************

	* ``EPSG`` :   ``<class 'int'>``   *<optional>*
		Description: integer code for coordinate transform of hydro-model, only used if running in  lon-lat mode and code not in hindcast, eg. EPSG for New Zealand Transverse Mercator 2000 = 2193, find codes at https://spatialreference.org/

		- default: ``None``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``dimension_map``: nested parameter dictionary
		* ``cols`` :   ``<class 'str'>`` **<isrequired>**
			Description: Column dimension name, x cord of grid

			- default: ``cols``

		* ``rows`` :   ``<class 'str'>`` **<isrequired>**
			Description: Row dimension name ie y cord of grid

			- default: ``rows``

		* ``time`` :   ``<class 'str'>`` **<isrequired>**
			- default: ``time``

		* ``vector2D`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

		* ``vector3D`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

		* ``z`` :   ``<class 'str'>``   *<optional>*
			Description: name of dim for vertical layer boundaries

			- default: ``None``

		* ``z_water_velocity`` :   ``<class 'str'>``   *<optional>*
			Description: z dimension of water velocity

			- default: ``z``

	* ``field_variable_map``: nested parameter dictionary
		* ``A_Z_profile`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files

			- default: ``None``

		* ``bottom_stress`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``None``

		* ``salinity`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``None``

		* ``tide`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``None``

		* ``water_depth`` :   ``<class 'str'>`` **<isrequired>**
			Description: maps standard internal field name to file variable name

			- default: ``None``

		* ``water_temperature`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``None``

		* ``water_velocity``:**<isrequired>**
			Description: - maps standard internal field name to file variable names for velocity components

			- a list containing type:  ``[<class 'str'>, None]``
			- default list : ``[]``
			- can_be_empty_list: ``True``
			- fixed_len: ``3``

		* ``water_velocity_depth_averaged``:  *<optional>*
			Description: - maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available

			- a list containing type:  ``[<class 'str'>]``
			- default list : ``[]``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``

		* ``wind_stress`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``None``

	* ``field_variables``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``
		- obsolete: `` parameter obsolete, use "load_fields" parameter, with field_variable_map if needed``

	* ``file_mask`` :   ``<class 'str'>`` **<isrequired>**
		Description: Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern

		- default: ``None``

	* ``grid_variable_map``: nested parameter dictionary
		* ``is_dry_cell`` :   ``<class 'numpy.int8'>``   *<optional>*
			Description: Time variable flag of when cell is dry, 1= is dry cell

			- default: ``None``

		* ``time`` :   ``<class 'str'>`` **<isrequired>**
			Description: time variable nae in file

			- default: ``time``

		* ``x``:**<isrequired>**
			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['x', 'y']``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``

		* ``zlevel`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

	* ``hydro_model_cords_in_lat_long`` :   ``<class 'bool'>``   *<optional>*
		Description: Force conversion given nodal lat longs to a UTM metres grid, only used if lat long coordinates not auto detected

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``input_dir`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``

	* ``isodate_of_hindcast_time_zero`` :   ``iso8601date``   *<optional>*
		Description: use to offset times to required times zone

		- default: ``None``

	* ``load_fields``:  *<optional>*
		Description: - A list of names of any additional variables to read and interplolate to give particle values, eg. a concentration field (water_veloctiy, tide and water_depth fields are always loaded). If a given name is in field_variable_map, then the mapped file variables will be used internally and in output. If not the given file variable name will be used internally and in particle property output. For any additional vector fields user must supply a file variable map in the "field_variable_map" parameter

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``max_numb_files_to_load`` :   ``<class 'int'>``   *<optional>*
		Description: Only read no more than this number of hindcast files, useful when setting up to speed run

		- default: ``10000000``
		- min: ``1``

	* ``one_based_indices`` :   ``<class 'bool'>``   *<optional>*
		Description: indices in hindcast start at 1, not zero, eg. triangulation nodes start at 1 not zero as in python

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``time_buffer_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``24``
		- min: ``2``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``vertical_regrid`` :   ``<class 'bool'>``   *<optional>*
		Description: Convert vertical grid to same sigma levels across domain

		- default: ``True``
		- possible_values: ``[True, False]``


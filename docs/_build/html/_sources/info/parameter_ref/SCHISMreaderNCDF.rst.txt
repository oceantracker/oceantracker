#################
SCHISMreaderNCDF
#################

**Doc:** 

**short class_name:** SCHISMreaderNCDF

**full class_name :** oceantracker.reader.schism_reader.SCHISMreaderNCDF

**Inheritance:** > ParameterBaseClass> _BaseReader> SCHISMreaderNCDF


Parameters:
************

	* ``EPSG`` :   ``<class 'int'>``   *<optional>*
		Description: integer code for coordinate transform of hydro-model, only used if running in  lon-lat mode and code not in hindcast, eg. EPSG for New Zealand Transverse Mercator 2000 = 2193, find codes at https://spatialreference.org/

		- default: ``None``
		- required_type: ``<class 'int'>``
		- expert: ``False``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``field_variable_map``: nested parameter dictionary

Parameters:
************

		* ``A_Z_profile`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name for turbulent eddy viscosity, used if present in files

			- default: ``diffusivity``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``bottom_stress`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``bottom_stress``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``salinity`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``salt``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``tide`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``elev``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``water_depth`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``depth``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``water_temperature`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``temp``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``water_velocity``:  *<optional>*
			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['hvel', 'vertical_velocity']``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``
			- expert: ``False``

		* ``water_velocity_depth_averaged``:  *<optional>*
			Description: - maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available

			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['dahv']``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``
			- expert: ``False``

		* ``wind_stress`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``wind_stress``
			- required_type: ``<class 'str'>``
			- expert: ``False``

	* ``field_variables``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``
		- obsolete: `` parameter obsolete, use "load_fields" parameter, with field_variable_map if needed``
		- expert: ``False``

	* ``file_mask`` :   ``<class 'str'>`` **<isrequired>**
		Description: Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``grid_variable_map``: nested parameter dictionary

Parameters:
************

		* ``bottom_cell_index`` :   ``<class 'str'>``   *<optional>*
			- default: ``node_bottom_index``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``is_dry_cell`` :   ``<class 'numpy.int8'>``   *<optional>*
			Description: Time variable flag of when cell is dry, 1= is dry cell

			- default: ``wetdry_elem``
			- required_type: ``<class 'numpy.int8'>``
			- expert: ``False``

		* ``time`` :   ``<class 'str'>``   *<optional>*
			- default: ``time``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``triangles`` :   ``<class 'str'>``   *<optional>*
			- default: ``SCHISM_hgrid_face_nodes``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``x``:  *<optional>*
			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y']``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``
			- expert: ``False``

		* ``zlevel`` :   ``<class 'str'>``   *<optional>*
			- default: ``zcor``
			- required_type: ``<class 'str'>``
			- expert: ``False``

	* ``hgrid_file_name`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``hydro_model_cords_in_lat_long`` :   ``<class 'bool'>``   *<optional>*
		Description: Force conversion given nodal lat longs to a UTM metres grid, only used if lat long coordinates not auto detected

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``
		- expert: ``False``

	* ``input_dir`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``load_fields``:  *<optional>*
		Description: - A list of names of any additional variables to read and interplolate to give particle values, eg. a concentration field (water_veloctiy, tide and water_depth fields are always loaded). If a given name is in field_variable_map, then the mapped file variables will be used internally and in output. If not the given file variable name will be used internally and in particle property output. For any additional vector fields user must supply a file variable map in the "field_variable_map" parameter

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``
		- expert: ``False``

	* ``max_numb_files_to_load`` :   ``<class 'int'>``   *<optional>*
		Description: Only read no more than this number of hindcast files, useful when setting up to speed run

		- default: ``10000000``
		- required_type: ``<class 'int'>``
		- min: ``1``
		- expert: ``False``

	* ``time_buffer_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``24``
		- required_type: ``<class 'int'>``
		- min: ``2``
		- expert: ``False``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``
		- required_type: ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``
		- expert: ``False``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``vertical_regrid`` :   ``<class 'bool'>``   *<optional>*
		Description: Convert vertical grid to same sigma levels across domain

		- default: ``True``
		- required_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``
		- expert: ``False``



Expert Parameters:
*******************



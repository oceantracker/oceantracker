############
dev_DELFTFM
############

**Doc:** 

**short class_name:** dev_DELFTFM

**full class_name :** oceantracker.reader.delft_fm.dev_DELFTFM


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseReader> dev_DELFTFM


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

			- default: ``mesh2d_s1``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``water_depth`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``mesh2d_node_z``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``water_temperature`` :   ``<class 'str'>``   *<optional>*
			Description: maps standard internal field name to file variable name

			- default: ``temp``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``water_velocity``:  *<optional>*
			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['mesh2d_ucx', 'mesh2d_ucy', 'mesh2d_ucz']``
			- can_be_empty_list: ``True``
			- fixed_len: ``3``
			- expert: ``False``

		* ``water_velocity_depth_averaged``:  *<optional>*
			Description: - maps standard internal field name to file variable names for depth averaged velocity components, used if 3D "water_velocity" variables not available

			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['mesh2d_ucx', 'mesh2d_ucy']``
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
			- default: ``None``
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
			- default: ``mesh2d_face_nodes``
			- required_type: ``<class 'str'>``
			- expert: ``False``

		* ``x``:  *<optional>*
			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['mesh2d_node_x', 'mesh2d_node_y']``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``
			- expert: ``False``

		* ``x_cell``:  *<optional>*
			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['mesh2d_face_x', 'mesh2d_face_y']``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``
			- expert: ``False``

		* ``zlevel`` :   ``<class 'str'>``   *<optional>*
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
		Description: - always load tide and water depth, for dry cells id 2D

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['water_depth']``
		- can_be_empty_list: ``True``
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



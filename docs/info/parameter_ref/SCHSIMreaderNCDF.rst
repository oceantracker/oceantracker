#################
SCHSIMreaderNCDF
#################

**Description:** Reads SCHISM netCDF output files

**Class:** oceantracker.reader.schism_reader.SCHSIMreaderNCDF

**File:** oceantracker/reader/schism_reader.py

**Inheritance:** _BaseReader> GenericUnstructuredReader> SCHSIMreaderNCDF

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``cords_in_lat_long`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``depth_average`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``dimension_map``: nested parameter dictionary
		* ``node`` :   ``<class 'str'>``   *<optional>*
			- default: ``nSCHISM_hgrid_node``

		* ``time`` :   ``<class 'str'>``   *<optional>*
			- default: ``time``

		* ``vector2Ddim`` :   ``<class 'str'>``   *<optional>*
			- default: ``two``

		* ``vector3Ddim`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

		* ``z`` :   ``<class 'str'>``   *<optional>*
			- default: ``nSCHISM_vgrid_layers``

	* ``field_variables``: nested parameter dictionary
		* ``salinity`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

		* ``tide`` :   ``<class 'str'>``   *<optional>*
			- default: ``elev``

		* ``water_depth`` :   ``<class 'str'>``   *<optional>*
			- default: ``depth``

		* ``water_temperature`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

		* ``water_velocity``:  *<optional>*
			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['hvel']``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``

	* ``field_variables_to_depth_average``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``

	* ``file_mask`` :   ``<class 'str'>`` **<isrequired>**
		Description: - Mask for file names, eg "scout*.nc", is joined with "input_dir" to give full file names

		- default: ``None``

	* ``grid_variables``: nested parameter dictionary
		* ``bottom_cell_index`` :   ``<class 'str'>``   *<optional>*
			- default: ``node_bottom_index``

		* ``is_dry_cell`` :   ``<class 'str'>``   *<optional>*
			Description: - Time variable flag of when cell is dry, 1= is dry cell

			- default: ``wetdry_elem``

		* ``time`` :   ``<class 'str'>``   *<optional>*
			- default: ``time``

		* ``triangles`` :   ``<class 'str'>``   *<optional>*
			- default: ``SCHISM_hgrid_face_nodes``

		* ``x``:  *<optional>*
			- a list containing type:  ``[<class 'str'>]``
			- default list : ``['SCHISM_hgrid_node_x', 'SCHISM_hgrid_node_y']``
			- can_be_empty_list: ``True``
			- fixed_len: ``2``

		* ``zlevel`` :   ``<class 'str'>``   *<optional>*
			- default: ``zcor``

	* ``hgrid_file_name`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``input_dir`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``isodate_of_hindcast_time_zero`` :   ``iso8601date``   *<optional>*
		- default: ``1970-01-01``

	* ``max_numb_files_to_load`` :   ``<class 'int'>``   *<optional>*
		- default: ``10000000``
		- min: ``1``

	* ``minimum_total_water_depth`` :   ``<class 'float'>``   *<optional>*
		Description: - Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering

		- default: ``0.25``
		- min: ``0.0``

	* ``name`` :   ``random_walk_varyingAz``   *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- default: ``None``

	* ``one_based_indices`` :   ``<class 'bool'>``   *<optional>*
		Description: - schism indcies are 1 based , not zero, eg. triangulation nodes start at 1 not zero as in python

		- default: ``True``
		- possible_values: ``[True, False]``

	* ``search_sub_dirs`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``time_buffer_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``48``
		- min: ``2``

	* ``time_zone`` :   ``<class 'int'>``   *<optional>*
		- default: ``None``
		- min: ``-12``
		- max: ``23``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


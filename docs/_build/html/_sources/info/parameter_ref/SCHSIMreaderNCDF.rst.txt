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

	* ``coordinate_projection`` :   ``<class 'str'>``   *<optional>*
		Description: - string map project for meters grid for use by pyproj module, eg  "proj=utm +zone=16 +datum=NAD83"

		- default: ``None``

	* ``cords_in_lat_long`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``depth_average`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``dimension_map``: nested parameter dictionary
	* ``field_variables``: nested parameter dictionary
		* ``bottom_stress`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

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

		* ``wind_stress`` :   ``<class 'str'>``   *<optional>*
			- default: ``None``

	* ``field_variables_to_depth_average``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``

	* ``file_mask`` :   ``<class 'str'>`` **<isrequired>**
		Description: - Mask for file names, eg "scout*.nc", is joined with "input_dir" to give full file names

		- default: ``None``

	* ``grid_file`` :   ``<class 'str'>``   *<optional>*
		Description: - File name with hydrodynamic grid data, as path relative to input_dir, default is get grid from first hindasct file

		- default: ``None``

	* ``grid_variables``: nested parameter dictionary
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

	* ``one_based_indices``: nested parameter dictionary
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

	* ``water_density`` :   ``<class 'int'>``   *<optional>*
		- default: ``48``
		- min: ``2``


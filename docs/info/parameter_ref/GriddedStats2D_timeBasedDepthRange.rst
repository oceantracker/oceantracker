###################################
GriddedStats2D_timeBasedDepthRange
###################################

**Description:** 

**Class:** oceantracker.particle_statistics.statisics_in_water_depth_range.GriddedStats2D_timeBasedDepthRange

**File:** oceantracker/particle_statistics/statisics_in_water_depth_range.py

**Inheritance:** _BaseParticleLocationStats> GriddedStats2D_timeBased> WaterDepthRangeStats> GriddedStats2D_timeBasedDepthRange

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``calculation_interval``:  *<optional>*
		Description: - time in sec, between calculating statistics

		- type: ``<class 'float'>``
		- default: ``3600.0``

	* ``case_output_file_tag``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``stats_gridded_time_depth_range``

	* ``class_name``:  *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``count_status_equal_to``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``count_status_greater_than``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``dead``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``description``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``grid_center``:  *<optional>*
		- a list containing type:  ``<class 'float'>``
		- default list item: ``None``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``grid_size``:  *<optional>*
		- a list containing type:  ``<class 'int'>``
		- default list item: ``None``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``grid_span``:  *<optional>*
		- a list containing type:  ``<class 'float'>``
		- default list item: ``None``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``max_water_depth``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``1000000000.0``

	* ``min_depth``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``-1000000000.0``

	* ``name``:  *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- type: ``<class 'str'>``
		- default: ``None``

	* ``particle_property_list``:  *<optional>*
		- a list containing type:  ``<class 'str'>``
		- default list item: ``None``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``release_group_centered_grids``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``write``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``


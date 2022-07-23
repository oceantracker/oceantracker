##################################
GriddedStats2D_ageBasedDepthRange
##################################

**Class:** oceantracker.particle_statistics.statisics_in_water_depth_range.GriddedStats2D_ageBasedDepthRange

**File:** oceantracker/particle_statistics/statisics_in_water_depth_range.py

**Inheritance:** BaseParticleLocationStats> GriddedStats2D_timeBased> GriddedStats2D_agedBased> WaterDepthRangeStats> GriddedStats2D_ageBasedDepthRange

**Default internal name:** ``"not given in defaults"``

**Description:** 


Parameters:
************

	* ``age_bin_size``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``86400.0``

	* ``calculation_interval``:  *<optional>*
		**Description:** - time in sec, between calculating statistics

		- type: ``<class 'float'>``
		- default: ``3600.0``

	* ``case_output_file_tag``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``stats_gridded_age_depth_range``

	* ``class_name``:  *<optional>*
		**Description:** - Class name as string A.B.C, used to import this class from python path

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

	* ``doc_str``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``grid_center``:  *<optional>*
		- a list containing type:  ``<class 'float'>``
		- default list item: ``None``
		- self: ``<oceantracker.util.parameter_checking.ParameterListChecker object at 0x0000029B1D014DC0>``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``grid_size``:  *<optional>*
		- a list containing type:  ``<class 'int'>``
		- default list item: ``None``
		- self: ``<oceantracker.util.parameter_checking.ParameterListChecker object at 0x0000029B1D014D00>``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``grid_span``:  *<optional>*
		- a list containing type:  ``<class 'float'>``
		- default list item: ``None``
		- self: ``<oceantracker.util.parameter_checking.ParameterListChecker object at 0x0000029B1D014DF0>``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``max_age_to_bin``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``2592000.0``

	* ``max_water_depth``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``1000000000.0``

	* ``min_age_to_bin``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``0.0``

	* ``min_depth``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``-1000000000.0``

	* ``name``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``particle_property_list``:  *<optional>*
		- a list containing type:  ``<class 'str'>``
		- default list item: ``None``
		- self: ``<oceantracker.util.parameter_checking.ParameterListChecker object at 0x0000029B1D014F10>``
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


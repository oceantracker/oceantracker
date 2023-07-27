#########################
GriddedStats2D_timeBased
#########################

**Description:** 

**class_name:** oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased

**File:** oceantracker/particle_statistics/gridded_statistics.py

**Inheritance:** _BaseParticleLocationStats> GriddedStats2D_timeBased


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``count_end_date`` :   ``iso8601date``   *<optional>*
		Description: Stop particle counting from this date

		- default: ``None``

	* ``count_start_date`` :   ``iso8601date``   *<optional>*
		Description: Start particle counting from this date

		- default: ``None``

	* ``grid_center``:  *<optional>*
		- a list containing type:  ``[<class 'float'>, <class 'int'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``grid_size``:  *<optional>*
		- a list containing type:  ``[<class 'int'>]``
		- default list : ``[100, 99]``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``grid_span``:  *<optional>*
		- a list containing type:  ``[<class 'float'>, <class 'int'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``particle_property_list``:  *<optional>*
		Description: - Create statistics for these named particle properties, list = ["water_depth"], for statics on water depth at particle locations inside the counted regions

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``release_group_centered_grids`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``stats_gridded_time``

	* ``status_max`` :   ``[<class 'str'>]``   *<optional>*
		Description: Count only those particles with status  <= to this value

		- default: ``moving``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``status_min`` :   ``[<class 'str'>]``   *<optional>*
		Description: Count only those particles with status >= to thsi value

		- default: ``frozen``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between calculating statistics

		- default: ``3600.0``
		- units: ``sec``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write statistcs to disk

		- default: ``True``
		- possible_values: ``[True, False]``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position <= to this value

		- default: ``1e+32``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position >=  to this value

		- default: ``-1e+32``


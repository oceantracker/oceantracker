########################
PolygonStats2D_ageBased
########################

**Description:** 

**class_name:** oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased

**File:** oceantracker/particle_statistics/polygon_statistics.py

**Inheritance:** _BaseParticleLocationStats> GriddedStats2D_timeBased> GriddedStats2D_agedBased> _CorePolygonMethods> PolygonStats2D_ageBased


Parameters:
************

	* ``age_bin_size`` :   ``<class 'float'>``   *<optional>*
		- default: ``86400.0``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``count_end_date`` :   ``iso8601date``   *<optional>*
		Description: Stop particle counting from this date

		- default: ``None``

	* ``count_start_date`` :   ``iso8601date``   *<optional>*
		Description: Start particle counting from this date

		- default: ``None``

	* ``grid_size``:  *<optional>*
		- a list containing type:  ``[<class 'int'>]``
		- default list : ``[100, 99]``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``

	* ``max_age_to_bin`` :   ``<class 'float'>``   *<optional>*
		- default: ``2592000.0``

	* ``min_age_to_bin`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``

	* ``particle_property_list``:  *<optional>*
		Description: - Create statistics for these named particle properties, list = ["water_depth"], for statics on water depth at particle locations inside the counted regions

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``polygon_list``:**<isrequired>**

polygon_list: still working on display  of lists of dict, eg nested polygon list 

	* ``requires_3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``stats_polygon_age``

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
		Description: Count only those particles with vertical positions <= to this value

		- default: ``1e+32``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical positions >=  to this value

		- default: ``-1e+32``


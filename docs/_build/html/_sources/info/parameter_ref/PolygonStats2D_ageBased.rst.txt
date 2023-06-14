########################
PolygonStats2D_ageBased
########################

**Description:** 

**Class:** oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased

**File:** oceantracker/particle_statistics/polygon_statistics.py

**Inheritance:** _BaseParticleLocationStats> GriddedStats2D_timeBased> GriddedStats2D_agedBased> _CorePolygonMethods> PolygonStats2D_ageBased


Parameters:
************

	* ``age_bin_size`` :   ``<class 'float'>``   *<optional>*
		- default: ``86400.0``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``count_end_date`` :   ``iso8601date``   *<optional>*
		Description: - Stop particle counting from this date

		- default: ``None``

	* ``count_start_date`` :   ``iso8601date``   *<optional>*
		Description: - Start particle counting from this date

		- default: ``None``

	* ``count_status_in_range``:  *<optional>*
		Description: - Count only those particles with status which fall in the given range

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['frozen', 'moving']``
		- can_be_empty_list: ``True``
		- min_length: ``2``
		- max_length: ``2``

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

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: - Time in seconds between calculating statistics

		- default: ``3600.0``
		- units: ``sec``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


#########################
PolygonStats2D_timeBased
#########################

**Description:** 

**Class:** oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased

**File:** oceantracker/particle_statistics/polygon_statistics.py

**Inheritance:** _BaseParticleLocationStats> GriddedStats2D_timeBased> _CorePolygonMethods> PolygonStats2D_timeBased

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``calculation_interval`` :   ``<class 'float'>``   *<optional>*
		Description: - time in sec, between calculating statistics

		- default: ``3600.0``

	* ``case_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``stats_polygon_time``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``count_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``count_status_greater_than`` :   ``<class 'str'>``   *<optional>*
		- default: ``dead``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``description`` :   ``<class 'str'>``   *<optional>*
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

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- default: ``None``

	* ``particle_property_list``:  *<optional>*
		- a list containing type:  ``<class 'str'>``
		- default list item: ``None``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``polygon_list``:  *<optional>*

polygon_list: still working on display  of lists of dict, eg nested polygon list 

	* ``release_group_centered_grids`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


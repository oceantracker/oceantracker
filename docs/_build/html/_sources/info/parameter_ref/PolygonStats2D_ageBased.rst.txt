########################
PolygonStats2D_ageBased
########################

**Description:** 

**Class:** oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased

**File:** oceantracker/particle_statistics/polygon_statistics.py

**Inheritance:** _BaseParticleLocationStats> GriddedStats2D_timeBased> GriddedStats2D_agedBased> _CorePolygonMethods> PolygonStats2D_ageBased

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``age_bin_size`` :   ``<class 'float'>``   *<optional>*
		- default: ``86400.0``

	* ``calculation_interval`` :   ``<class 'float'>``   *<optional>*
		Description: - time in sec, between calculating statistics

		- default: ``3600.0``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``count_status_in_range``:  *<optional>*
		Description: - Count only those particles with status which fall in the given range

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['frozen', 'moving']``
		- can_be_empty_list: ``True``
		- min_length: ``2``
		- max_length: ``2``

	* ``file_tag`` :   ``<class 'str'>``   *<optional>*
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

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- default: ``None``

	* ``particle_property_list``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``polygon_list``:**<isrequired>**

polygon_list: still working on display  of lists of dict, eg nested polygon list 

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``stats_polygon_age``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


####################
TopBottomLayerStats
####################

**Description:** 

**Class:** oceantracker.particle_statistics.statisics_in_top_or_bottom_layer.TopBottomLayerStats

**File:** oceantracker/particle_statistics/statisics_in_top_or_bottom_layer.py

**Inheritance:** TopBottomLayerStats

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``layer_thick_ness`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``
		- min: ``0.0``

	* ``max_status`` :   ``<class 'str'>``   *<optional>*
		- default: ``moving``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``min_status`` :   ``<class 'str'>``   *<optional>*
		- default: ``frozen``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- default: ``None``

	* ``top_layer`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


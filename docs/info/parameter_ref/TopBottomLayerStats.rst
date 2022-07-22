####################
TopBottomLayerStats
####################

**Class:** oceantracker.particle_statistics.statisics_in_top_or_bottom_layer.TopBottomLayerStats

**File:** oceantracker/particle_statistics/statisics_in_top_or_bottom_layer.py

**Inheritance:** TopBottomLayerStats

**Default internal name:** ``"not given in defaults"``

**Description:** 


Parameters:
************

	* ``class_name``:  *<optional>*
		**Description:** - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``doc_str``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``layer_thick_ness``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``0.0``
		- min: ``0.0``

	* ``max_status``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``moving``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``min_status``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``frozen``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``name``:  *<optional>*
		**Description:** - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- type: ``<class 'str'>``
		- default: ``None``

	* ``top_layer``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


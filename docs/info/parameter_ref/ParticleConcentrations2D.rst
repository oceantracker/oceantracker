#########################
ParticleConcentrations2D
#########################

**Description:** 

**class_name:** oceantracker.particle_concentrations.particle_concentrations.ParticleConcentrations2D

**File:** oceantracker/particle_concentrations/particle_concentrations.py

**Inheritance:** _BaseTriangleProperties> ParticleConcentrations2D


Parameters:
************

	* ``class_name`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``

	* ``count_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``only_update_concentrations_on_write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``output_step_count`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``particle_properties_to_track``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``release_group_to_track`` :   ``<class 'int'>``   *<optional>*
		- default: ``None``
		- min: ``0``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``_concentrations_``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


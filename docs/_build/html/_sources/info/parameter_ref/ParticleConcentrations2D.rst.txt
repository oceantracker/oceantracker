#########################
ParticleConcentrations2D
#########################

**Class:** oceantracker.particle_concentrations.particle_concentrations.ParticleConcentrations2D

**File:** oceantracker/particle_concentrations/particle_concentrations.py

**Inheritance:** BaseTriangleProperties> ParticleConcentrations2D

**Default internal name:** ``"not given in defaults"``

**Description:** 


Parameters:
************

	* ``calculation_interval``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``1``
		- min: ``1``

	* ``case_output_file_tag``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	**<isrequired>**
		- type: ``<class 'str'>``
		- default: ``None``

	* ``count_status_equal_to``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``name``:  *<optional>*
		**Description:** - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- type: ``<class 'str'>``
		- default: ``None``

	* ``only_update_concentrations_on_write``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``output_step_count``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``1``
		- min: ``1``

	* ``particle_properties_to_track``:  *<optional>*
		- a list containing type:  ``<class 'str'>``
		- default list item: ``None``
		- self: ``<oceantracker.util.parameter_checking.ParameterListChecker object at 0x000002798ACC7A00>``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``release_group_to_track``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``None``
		- min: ``0``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``write``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``


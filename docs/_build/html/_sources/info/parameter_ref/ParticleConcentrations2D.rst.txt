#########################
ParticleConcentrations2D
#########################

**Doc:** 

**short class_name:** ParticleConcentrations2D

**full class_name :** oceantracker.particle_concentrations.particle_concentrations.ParticleConcentrations2D

**Inheritance:** > ParameterBaseClass> _BaseTriangleProperties> ParticleConcentrations2D


Parameters:
************

	* ``class_name`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``count_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- expert: ``False``

	* ``initial_particle_load`` :   ``<class 'float'>``   *<optional>*
		Description: initial load of particles on release

		- default: ``1.0``
		- required_type: ``<class 'float'>``
		- units: ``non-dimensional``
		- expert: ``False``

	* ``load_decay_time_scale`` :   ``<class 'float'>``   *<optional>*
		Description: time scale of exponential decay of particle load

		- default: ``86400``
		- required_type: ``<class 'float'>``
		- units: ``sec``
		- expert: ``False``

	* ``only_update_concentrations_on_write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- required_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``
		- expert: ``False``

	* ``particle_properties_to_track``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``
		- expert: ``False``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``_concentrations_``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``update_interval`` :   ``<class 'int'>``   *<optional>*
		Description: the time in model seconds between writes (will be rounded to model time step)

		- default: ``3600.0``
		- required_type: ``<class 'int'>``
		- min: ``1``
		- units: ``sec``
		- expert: ``False``

	* ``update_values_every_time_step`` :   ``<class 'bool'>``   *<optional>*
		Description: update values in memory every time step, needed if using concentrations within modelling to change particle behaviour or properties. Output interval still sep by update_interval

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- min: ``1``
		- units: ``sec``
		- possible_values: ``[True, False]``
		- expert: ``False``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``
		- required_type: ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``
		- expert: ``False``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- required_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``
		- expert: ``False``



Expert Parameters:
*******************



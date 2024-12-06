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
		- data_type: ``<class 'str'>``

	* ``count_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``initial_particle_load`` :   ``<class 'float'>``   *<optional>*
		Description: initial load of particles on release

		- default: ``1.0``
		- data_type: ``<class 'float'>``
		- units: ``non-dimensional``

	* ``load_decay_time_scale`` :   ``<class 'float'>``   *<optional>*
		Description: time scale of exponential decay of particle load

		- default: ``86400``
		- data_type: ``<class 'float'>``
		- units: ``sec``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``only_update_concentrations_on_write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``particle_properties_to_track``:  *<optional>*
		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``True``
		- min_len: ``0``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``_concentrations_``
		- data_type: ``<class 'str'>``

	* ``update_interval`` :   ``<class 'int'>``   *<optional>*
		Description: the time in model seconds between writes (will be rounded to model time step)

		- default: ``3600.0``
		- data_type: ``<class 'int'>``
		- units: ``sec``
		- min: ``1``

	* ``update_values_every_time_step`` :   ``<class 'bool'>``   *<optional>*
		Description: update values in memory every time step, needed if using concentrations within modelling to change particle behaviour or properties. Output interval still sep by update_interval

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- units: ``sec``
		- min: ``1``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



Expert Parameters:
*******************



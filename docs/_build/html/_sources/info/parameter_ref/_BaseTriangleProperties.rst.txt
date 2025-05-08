########################
_BaseTriangleProperties
########################

**Doc:** 

**short class_name:** _BaseTriangleProperties

**full class_name :** oceantracker.particle_concentrations._base_user_triangle_properties._BaseTriangleProperties


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseTriangleProperties


Parameters:
************

	* ``class_name`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``count_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'notReleased', 'dead', 'outside_open_boundary', 'outside_domain', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

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



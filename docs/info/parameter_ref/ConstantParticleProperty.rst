#########################
ConstantParticleProperty
#########################

**Description:** Constant particle property which does not vary in time, which can be used to calculate spatial and temporal statistics from particle properties

**class_name:** oceantracker.particle_properties.constant_part_prop.ConstantParticleProperty

**File:** oceantracker/particle_properties/constant_part_prop.py

**Inheritance:** _BasePropertyInfo> ParticleProperty> ConstantParticleProperty


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``dtype`` :   ``<class 'numpy.dtype'>``   *<optional>*
		- default: ``<class 'numpy.float64'>``

	* ``fill_value`` :   ``[<class 'int'>, <class 'float'>]``   *<optional>*
		- default: ``None``

	* ``initial_value`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``

	* ``prop_dim3`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``requires_3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``type`` :   ``<class 'str'>``   *<optional>*
		Description: particle property

		- default: ``user``
		- possible_values: ``['manual_update', 'from_fields', 'user']``

	* ``update`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``value`` :   ``<class 'float'>``   *<optional>*
		Description: Value of the particle property for each particle which does not vary with time

		- default: ``1.0``

	* ``variance`` :   ``<class 'float'>``   *<optional>*
		Description: Optional variance of the value given to each individual particle, which then does not vary in time, drawn from normal distribution, with mean "value"  and given variance

		- default: ``None``
		- min: ``0.0``

	* ``vector_dim`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


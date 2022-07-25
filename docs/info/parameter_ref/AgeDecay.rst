#########
AgeDecay
#########

**Description:** Exponentially decaying particle property based on age.

**Class:** oceantracker.particle_properties.age_decay.AgeDecay

**File:** oceantracker/particle_properties/age_decay.py

**Inheritance:** _BasePropertyInfo> ParticleProperty> AgeDecay

**Default internal name:** ``"age_decay"``


Parameters:
************

	* ``class_name``:  *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``decay_time_scale``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``86400.0``

	* ``description``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``dtype``:  *<optional>*
		- type: ``<class 'type'>``
		- default: ``<class 'numpy.float64'>``
		- possible_values: ``[<class 'numpy.float32'>, <class 'numpy.float64'>, <class 'numpy.int8'>, <class 'numpy.int16'>, <class 'numpy.int32'>, <class 'bool'>]``

	* ``initial_value``:  *<optional>*
		Description: - Particle property at the time of release

		- type: ``<class 'float'>``
		- default: ``1.0``

	* ``name``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``age_decay``

	* ``prop_dim3``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``1``
		- min: ``1``

	* ``time_varying``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``type``:  *<optional>*
		Description: - particle property

		- type: ``<class 'str'>``
		- default: ``user``
		- possible_values: ``['manual_update', 'from_fields', 'user']``

	* ``update``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``vector_dim``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``1``
		- min: ``1``

	* ``write``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``


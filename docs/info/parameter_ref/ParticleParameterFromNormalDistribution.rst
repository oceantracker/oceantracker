########################################
ParticleParameterFromNormalDistribution
########################################

**Description:** 

**Class:** oceantracker.particle_properties.particle_parameter_from_normal_distribution.ParticleParameterFromNormalDistribution

**File:** oceantracker/particle_properties/particle_parameter_from_normal_distribution.py

**Inheritance:** _BasePropertyInfo> ParticleProperty> ParticleParameterFromNormalDistribution

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``dtype`` :   ``<class 'numpy.dtype'>``   *<optional>*
		- default: ``<class 'numpy.float64'>``

	* ``initial_value`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``

	* ``mean`` :   ``<class 'float'>`` **<isrequired>**
		- default: ``0.0``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``prop_dim3`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``type`` :   ``<class 'str'>``   *<optional>*
		Description: - particle property

		- default: ``user``
		- possible_values: ``['manual_update', 'from_fields', 'user']``

	* ``update`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``variance`` :   ``<class 'float'>`` **<isrequired>**
		- default: ``0.0``
		- min: ``0.0``

	* ``vector_dim`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


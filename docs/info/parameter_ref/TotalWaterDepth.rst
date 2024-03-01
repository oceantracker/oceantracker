################
TotalWaterDepth
################

**Description:** 

**class_name:** oceantracker.particle_properties.total_water_depth.TotalWaterDepth

**File:** oceantracker/particle_properties/total_water_depth.py

**Inheritance:** _BaseParticleProperty> ParticleProperty> TotalWaterDepth


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

	* ``is3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``prop_dim3`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``release_group_parameters`` :   ``<class 'list'>``   *<optional>*
		Description: In development: release group specific particle prop params

		- default: ``[]``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``type`` :   ``<class 'str'>``   *<optional>*
		Description: type of particle property, used to manage how to update particle property

		- default: ``user``
		- possible_values: ``['manual_update', 'from_fields', 'user']``

	* ``update`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``vector_dim`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write particle property to tracks or event files file

		- default: ``True``
		- possible_values: ``[True, False]``


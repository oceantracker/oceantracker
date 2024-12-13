################################
ManuallyUpdatedParticleProperty
################################

**Doc:** 

**short class_name:** ManuallyUpdatedParticleProperty

**full class_name :** oceantracker.particle_properties._base_particle_properties.ManuallyUpdatedParticleProperty

**Inheritance:** > ParameterBaseClass> _BaseParticleProperty> ManuallyUpdatedParticleProperty


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``dtype`` :   ``<class 'str'>``   *<optional>*
		- default: ``float64``
		- data_type: ``<class 'str'>``
		- possible_values: ``['float64', 'float32', 'bool', 'int32', 'int16', 'int8', 'int64']``

	* ``initial_value`` :   ``<class 'float'>``   *<optional>*
		Description: Value given to particle property on release

		- default: ``0.0``
		- data_type: ``<class 'float'>``

	* ``name`` :   ``<class 'str'>`` **<isrequired>**
		Description: Name used to refer to this particle property in code and output

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``prop_dim3`` :   ``<class 'int'>``   *<optional>*
		Description: size of a 3d dimesion of particle property

		- default: ``1``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``units`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``update`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``vector_dim`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write particle property to tracks or event files file

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



Expert Parameters:
*******************

	* ``release_group_parameters``:  *<optional>*
		Description: - In development: release group specific particle prop params

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``



#############
ParticleLoad
#############

**Doc:**     Particle property which carries a load or mass, which can be used to calculate spatial and temporal statistics of this load or mass.    

**short class_name:** ParticleLoad

**full class_name :** oceantracker.particle_properties.load_carrying.ParticleLoad

**Inheritance:** > ParameterBaseClass> _BaseParticleProperty> ParticleProperty> ParticleLoad


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``dtype`` :   ``<class 'numpy.dtype'>``   *<optional>*
		- default: ``<class 'numpy.float64'>``
		- required_type: ``<class 'numpy.dtype'>``
		- expert: ``False``

	* ``fill_value`` :   ``[<class 'int'>, <class 'float'>]``   *<optional>*
		- default: ``None``
		- required_type: ``[<class 'int'>, <class 'float'>]``
		- expert: ``False``

	* ``initial_value`` :   ``<class 'float'>``   *<optional>*
		Description: Value of the particle property when it is released

		- default: ``1.0``
		- required_type: ``<class 'float'>``
		- expert: ``False``

	* ``prop_dim3`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- required_type: ``<class 'int'>``
		- min: ``1``
		- expert: ``False``

	* ``release_group_parameters`` :   ``<class 'list'>``   *<optional>*
		Description: In development: release group specific particle prop params

		- default: ``[]``
		- required_type: ``<class 'list'>``
		- expert: ``False``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``type`` :   ``<class 'str'>``   *<optional>*
		Description: type of particle property, used to manage how to update particle property

		- default: ``user``
		- required_type: ``<class 'str'>``
		- possible_values: ``['manual_update', 'from_fields', 'user']``
		- expert: ``False``

	* ``units`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``update`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- required_type: ``<class 'bool'>``
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

	* ``vector_dim`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- required_type: ``<class 'int'>``
		- min: ``1``
		- expert: ``False``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write particle property to tracks or event files file

		- default: ``True``
		- required_type: ``<class 'bool'>``
		- expert: ``False``



Expert Parameters:
*******************



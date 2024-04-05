#####################
ParticleGroupManager
#####################

**Doc:** 

**short class_name:** ParticleGroupManager

**full class_name :** oceantracker.particle_group_manager.particle_group_manager.ParticleGroupManager

**Inheritance:** > ParameterBaseClass> ParticleGroupManager


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``particle_buffer_chunk_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``500000``
		- required_type: ``<class 'int'>``
		- min: ``1``
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



Expert Parameters:
*******************



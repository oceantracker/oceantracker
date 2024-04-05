###############
SplitParticles
###############

**Doc:** 

**short class_name:** SplitParticles

**full class_name :** oceantracker.trajectory_modifiers.split_particles.SplitParticles

**Inheritance:** > ParameterBaseClass> _BaseTrajectoryModifier> SplitParticles


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``probability_of_splitting`` :   ``<class 'float'>``   *<optional>*
		- default: ``1.0``
		- required_type: ``<class 'float'>``
		- min: ``0.0``
		- max: ``1.0``
		- expert: ``False``

	* ``split_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- expert: ``False``

	* ``split_status_greater_than`` :   ``<class 'str'>``   *<optional>*
		- default: ``dead``
		- required_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- expert: ``False``

	* ``splitting_interval`` :   ``<class 'float'>``   *<optional>*
		- default: ``3600``
		- required_type: ``<class 'float'>``
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



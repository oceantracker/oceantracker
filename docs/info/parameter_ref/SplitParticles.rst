###############
SplitParticles
###############

**Description:** 

**full class_name :** oceantracker.trajectory_modifiers.split_particles.SplitParticles

**short class_name:** SplitParticles

docs>>

**Inheritance:** > ParameterBaseClass> _BaseTrajectoryModifier> SplitParticles


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``probability_of_splitting`` :   ``<class 'float'>``   *<optional>*
		- default: ``1.0``
		- min: ``0.0``
		- max: ``1.0``

	* ``split_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``split_status_greater_than`` :   ``<class 'str'>``   *<optional>*
		- default: ``dead``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``splitting_interval`` :   ``<class 'float'>``   *<optional>*
		- default: ``3600``
		- min: ``1``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


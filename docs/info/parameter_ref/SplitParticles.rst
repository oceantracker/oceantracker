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
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``probability_of_splitting`` :   ``<class 'float'>``   *<optional>*
		- default: ``1.0``
		- default: ``1.0``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``0.0``
		- max: ``1.0``

	* ``split_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``split_status_greater_than`` :   ``<class 'str'>``   *<optional>*
		- default: ``dead``
		- default: ``dead``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``splitting_interval`` :   ``<class 'float'>``   *<optional>*
		- default: ``3600``
		- default: ``3600``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``1``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``



Expert Parameters:
*******************



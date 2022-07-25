###############
SplitParticles
###############

**Description:** 

**Class:** oceantracker.trajectory_modifiers.split_particles.SplitParticles

**File:** oceantracker/trajectory_modifiers/split_particles.py

**Inheritance:** _BaseTrajectoryModifier> SplitParticles

**Default internal name:** ``"particle_splitting"``


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		- default: ``particle_splitting``

	* ``probability_of_splitting`` :   ``<class 'float'>``   *<optional>*
		- default: ``1.0``
		- min: ``0.0``
		- max: ``1.0``

	* ``requires_3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``split_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``split_status_greater_than`` :   ``<class 'str'>``   *<optional>*
		- default: ``dead``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``splitting_interval`` :   ``<class 'float'>``   *<optional>*
		- default: ``3600``
		- min: ``1``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


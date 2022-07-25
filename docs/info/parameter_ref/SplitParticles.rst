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

	* ``class_name``:  *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``description``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``name``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``particle_splitting``

	* ``probability_of_splitting``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``1.0``
		- min: ``0.0``
		- max: ``1.0``

	* ``requires_3D``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``split_status_equal_to``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``split_status_greater_than``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``dead``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``splitting_interval``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``3600``
		- min: ``1``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


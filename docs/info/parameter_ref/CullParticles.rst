##############
CullParticles
##############

**Description:** 

**Class:** oceantracker.trajectory_modifiers.cull_particles.CullParticles

**File:** oceantracker/trajectory_modifiers/cull_particles.py

**Inheritance:** _BaseTrajectoryModifier> CullParticles

**Default internal name:** ``"ParticleKill"``


Parameters:
************

	* ``class_name``:  *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``cull_interval``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``86400``
		- min: ``0``

	* ``cull_status_equal_to``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``cull_status_greater_than``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``dead``
		- possible_values: ``dict_keys(['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving'])``

	* ``description``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``name``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``ParticleKill``

	* ``probability_of_culling``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``0.1``
		- min: ``0``
		- max: ``1.0``

	* ``requires_3D``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


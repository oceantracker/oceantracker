##############
CullParticles
##############

**Doc:**     Prototype for how to  cull particles, this version just culls random particles,     inherit and change "def select_particles_to_cull(self, time_sec, active):" method to give other behaviors')    

**short class_name:** CullParticles

**full class_name :** oceantracker.trajectory_modifiers.cull_particles.CullParticles

**Inheritance:** > ParameterBaseClass> _BaseTrajectoryModifier> CullParticles


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``cull_interval`` :   ``<class 'float'>``   *<optional>*
		- default: ``86400``
		- default: ``86400``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``0``

	* ``cull_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``cull_status_greater_than`` :   ``<class 'str'>``   *<optional>*
		- default: ``dead``
		- default: ``dead``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``probability_of_culling`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.1``
		- default: ``0.1``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``0``
		- max: ``1.0``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``



Expert Parameters:
*******************



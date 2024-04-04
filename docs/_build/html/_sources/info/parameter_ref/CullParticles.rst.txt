##############
CullParticles
##############

**Description:** 

**full class_name :** oceantracker.trajectory_modifiers.cull_particles.CullParticles

**short class_name:** CullParticles

    Prototype for how to  cull particles, this version just culls random particles,     inherit and change "def select_particles_to_cull(self, time_sec, active):" method to give other behaviors')    

**Inheritance:** > ParameterBaseClass> _BaseTrajectoryModifier> CullParticles


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``cull_interval`` :   ``<class 'float'>``   *<optional>*
		- default: ``86400``
		- min: ``0``

	* ``cull_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``cull_status_greater_than`` :   ``<class 'str'>``   *<optional>*
		- default: ``dead``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``probability_of_culling`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.1``
		- min: ``0``
		- max: ``1.0``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


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
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``cull_interval`` :   ``<class 'float'>``   *<optional>*
		- default: ``86400``
		- required_type: ``<class 'float'>``
		- min: ``0``
		- expert: ``False``

	* ``cull_status_equal_to`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- expert: ``False``

	* ``cull_status_greater_than`` :   ``<class 'str'>``   *<optional>*
		- default: ``dead``
		- required_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- expert: ``False``

	* ``probability_of_culling`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.1``
		- required_type: ``<class 'float'>``
		- min: ``0``
		- max: ``1.0``
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



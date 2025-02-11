#########
CullRate
#########

**Doc:**     Decays particle numbers by killing random selection of particles based at each time step give averagerate per second decay_rate.    Probability of single particle decay given by  (1-exp(-time_step*decay_rate), for small time steps prob. is approx. time_step*decay_rate    

**short class_name:** CullRate

**full class_name :** oceantracker.trajectory_modifiers.cull_rate.CullRate

**Inheritance:** > ParameterBaseClass> _BaseTrajectoryModifier> CullRate


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``decay_rate`` :   ``<class 'float'>``   *<optional>*
		Description: Particles decay at this average rate

		- default: ``86400.0``
		- data_type: ``<class 'float'>``
		- units: ``particles per sec``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``



Expert Parameters:
*******************



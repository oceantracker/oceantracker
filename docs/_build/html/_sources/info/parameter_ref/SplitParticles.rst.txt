###############
SplitParticles
###############

**Doc:**     Splits  particles in two at  given time interval,    for given status values and  given particle age range.    Simulates reproduction, but can produce large numbers fast!    

**short class_name:** SplitParticles

**full class_name :** oceantracker.trajectory_modifiers.split_particles.SplitParticles

**Inheritance:** > ParameterBaseClass> _BaseTrajectoryModifier> SplitParticles


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``interval`` :   ``<class 'float'>``   *<optional>*
		Description: time interval between splits

		- default: ``86400``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``60``

	* ``max_age`` :   ``<class 'float'>``   *<optional>*
		Description: maximum particle age to split

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``sec``

	* ``min_age`` :   ``<class 'float'>``   *<optional>*
		Description: minumim particle age to start splitting

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``sec``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``probability`` :   ``<class 'float'>``   *<optional>*
		Description: probability of splitting at each given interval

		- default: ``1.0``
		- data_type: ``<class 'float'>``
		- min: ``0.0``
		- max: ``1.0``

	* ``statuses``:  *<optional>*
		Description: - list of status names to cull

		- a list containing type:  ``[]``
		- default list : ``['moving', 'on_bottom', 'stranded_by_tide', 'stationary']``
		- data_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``1``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``



Expert Parameters:
*******************



##############
CullParticles
##############

**Doc:**     Prototype for how to  cull particles,    this version just culls random particles of given statuses,     at given interval and start end times.    To give other behaviors inherit and change "def select_particles_to_cull(self, time_sec, active):" method')    

**short class_name:** CullParticles

**full class_name :** oceantracker.trajectory_modifiers.cull_particles.CullParticles

**Inheritance:** > ParameterBaseClass> _BaseTrajectoryModifier> CullParticles


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``end`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: date/time of last cull

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``interval`` :   ``<class 'float'>``   *<optional>*
		Description: time in seconds between culls, default 1 day

		- default: ``None``
		- data_type: ``<class 'float'>``
		- min: ``0``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``probability`` :   ``<class 'float'>``   *<optional>*
		- default: ``1.0``
		- data_type: ``<class 'float'>``
		- min: ``0``
		- max: ``1.0``

	* ``start`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: start date/time of first cull"

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

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



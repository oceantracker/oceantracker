########################
GriddedStats2D_ageBased
########################

**Doc:** 

**short class_name:** GriddedStats2D_ageBased

**full class_name :** oceantracker.particle_statistics.gridded_statistics2D.GriddedStats2D_ageBased


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseParticleLocationStats> GriddedStats2D_timeBased> GriddedStats2D_ageBased


Parameters:
************

	* ``age_bin_size`` :   ``<class 'float'>``   *<optional>*
		Description: Size of bins to count ages into, default= 1 week

		- default: ``604800.0``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``1``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``duration`` :   ``<class 'float'>``   *<optional>*
		Description: How long to do counting after start time, can be used instead of "end" parameter

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``0.0``

	* ``end`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: Stop particle counting from this iso date-time, default is end of model run

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``


grid_center: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``grid_size``:  *<optional>*
		Description: - number of (rows, columns) in grid, where rows is y size, cols x size, values should be odd, so will be rounded up to next

		- a list containing type:  ``[]``
		- default list : ``[100, 99]``
		- data_type: ``<class 'int'>``
		- min: ``1``
		- max: ``100000``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- fixed_len: ``2``
		- min_len: ``0``

	* ``grid_span``:**<isrequired>**
		Description: - (width-x, height-y)  of the statistics grid

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'float'>``
		- units: ``meters (dx,dy) or degrees (dlon, dlat) if geographic``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``max_age_to_bin`` :   ``<class 'float'>`` **<isrequired>**
		Description: Max. particle age to count

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``1.0``

	* ``min_age_to_bin`` :   ``<class 'float'>``   *<optional>*
		Description: Min. particle age to count

		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``0.0``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``near_seabed`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles within this distance of bottom

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``meters above seabed``
		- min: ``0.001``

	* ``near_seasurface`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles within this distance of tidal sea surface

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``meters below sea surface``
		- min: ``0.001``

	* ``particle_property_list``:  *<optional>*
		Description: - Create statistics for these named particle properties, list = ["water_depth"], for average of water depth at particle locations inside the counted regions

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``True``
		- min_len: ``0``

	* ``release_group_centered_grids`` :   ``<class 'bool'>``   *<optional>*
		Description: Center grid on the release groups  mean horizontal location or center of release polygon.

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``stats_gridded_age``
		- data_type: ``<class 'str'>``

	* ``start`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: Start particle counting from this date-time, default is start of model run

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``status_list``:  *<optional>*
		Description: - List of particle status types to count,eg  ["on_bottom","moving"], other status types will be ignored in statistcs

		- a list containing type:  ``[]``
		- default list : ``['stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- data_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'notReleased', 'dead', 'outside_domain', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between calculating statistics, wil be rounded to be a multiple of the particle tracking time step

		- default: ``3600.0``
		- data_type: ``<class 'float'>``
		- units: ``sec``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``water_depth_max`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles in water depths less than this value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- min: ``0.0``

	* ``water_depth_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles in water depths greater than this value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- min: ``0.0``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write statistcs to disk

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position <= to this value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``meters above mean water level, so is < 0 at depth``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position >=  to this value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``meters above mean water level, so is < 0 at depth``



Expert Parameters:
*******************



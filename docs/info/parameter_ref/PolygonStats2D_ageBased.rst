########################
PolygonStats2D_ageBased
########################

**Doc:** 

**short class_name:** PolygonStats2D_ageBased

**full class_name :** oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_ageBased

**Inheritance:** > ParameterBaseClass> _BaseParticleLocationStats> GriddedStats2D_timeBased> GriddedStats2D_ageBased> _CorePolygonMethods> PolygonStats2D_ageBased


Parameters:
************

	* ``age_bin_size`` :   ``<class 'float'>``   *<optional>*
		Description: Size of bins to count ages into, default= 1 week

		- default: ``604800.0``
		- data_type: ``<class 'float'>``
		- units: ``sec``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``coords_in_lat_lon_order`` :   ``<class 'bool'>``   *<optional>*
		Description: Allows points to be given (lat,lon) and order will be swapped before use, only used if hydro-model coords are in degrees

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

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

	* ``max_age_to_bin`` :   ``<class 'float'>``   *<optional>*
		Description: Max. particle age to count

		- default: ``1e+50``
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

	* ``particle_property_list``:  *<optional>*
		Description: - Create statistics for these named particle properties, list = ["water_depth"], for average of water depth at particle locations inside the counted regions

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``True``
		- min_len: ``0``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``stats_polygon_age``
		- data_type: ``<class 'str'>``

	* ``start`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: Start particle counting from this date-time, default is start of model run

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``status_max`` :   ``<class 'str'>``   *<optional>*
		Description: Count only those particles with status  <= to this value

		- default: ``moving``
		- data_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``status_min`` :   ``<class 'str'>``   *<optional>*
		Description: Count only those particles with status >= to this value

		- default: ``stationary``
		- data_type: ``<class 'str'>``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between calculating statistics, wil be rounded to be a multiple of the particle tracking time step

		- default: ``3600.0``
		- data_type: ``<class 'float'>``
		- units: ``sec``

	* ``use_release_group_polygons`` :   ``<class 'bool'>``   *<optional>*
		Description: Omit polygon_list param and use all polygon release polygons as statistics/counting polygons, useful for building release group polygon to polygon connectivity matrix.

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

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



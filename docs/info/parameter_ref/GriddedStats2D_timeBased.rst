#########################
GriddedStats2D_timeBased
#########################

**Doc:** 

**short class_name:** GriddedStats2D_timeBased

**full class_name :** oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased

**Inheritance:** > ParameterBaseClass> _BaseParticleLocationStats> GriddedStats2D_timeBased


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``coords_allowed_in_lat_lon_order`` :   ``<class 'bool'>``   *<optional>*
		Description: Allows points to be given (lat,lon) and order will be swapped before use, only used if hydro-model coords are in degrees

		- default: ``False``
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``

	* ``duration`` :   ``<class 'float'>``   *<optional>*
		Description: How long to do counting after start time, can be used instead of "end" parameter

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- units: ``sec``
		- min: ``0.0``

	* ``end`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: Stop particle counting from this iso date-time, default is end of model run

		- default: ``None``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``


grid_center: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``grid_size``:  *<optional>*
		Description: - number of rows and columns in grid

		- a list containing type:  ``[]``
		- default list : ``[100, 99]``
		- default: ``[100, 99]``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``1``
		- max: ``100000``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- fixed_len: ``2``
		- min_len: ``0``


grid_span: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``particle_property_list``:  *<optional>*
		Description: - Create statistics for these named particle properties, list = ["water_depth"], for average of water depth at particle locations inside the counted regions

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_types: ``[]``
		- make_list_unique: ``True``
		- min_len: ``0``

	* ``release_group_centered_grids`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``stats_gridded_time``
		- default: ``stats_gridded_time``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``start`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: Start particle counting from this date-time, default is start of model run

		- default: ``None``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``status_max`` :   ``<class 'str'>``   *<optional>*
		Description: Count only those particles with status  <= to this value

		- default: ``moving``
		- default: ``moving``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``status_min`` :   ``<class 'str'>``   *<optional>*
		Description: Count only those particles with status >= to this value

		- default: ``stationary``
		- default: ``stationary``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between calculating statistics, wil be rounded to be a multiple of the particle tracking time step

		- default: ``3600.0``
		- default: ``3600.0``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- units: ``sec``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``water_depth_max`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles in water depths less than this value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``0.0``

	* ``water_depth_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles in water depths greater than this value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``0.0``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write statistcs to disk

		- default: ``True``
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position <= to this value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- units: ``meters above mean water level, so is < 0 at depth``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position >=  to this value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- units: ``meters above mean water level, so is < 0 at depth``



Expert Parameters:
*******************



#########################
GriddedStats2D_timeBased
#########################

**Description:** 

**class_name:** oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased

**File:** oceantracker/particle_statistics/gridded_statistics.py

**Inheritance:** _BaseParticleLocationStats> GriddedStats2D_timeBased


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``coords_allowed_in_lat_lon_order`` :   ``<class 'bool'>``   *<optional>*
		Description: Allows points to be given (lat,lon) and order will be swapped before use, only used if hydro-model coords are in degrees

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``count_end_date`` :   ``iso8601date``   *<optional>*
		Description: Stop particle counting from this iso date-time

		- default: ``None``

	* ``count_start_date`` :   ``iso8601date``   *<optional>*
		Description: Start particle counting from this iso date-time

		- default: ``None``


grid_center: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``grid_size``:  *<optional>*
		Description: - number of rows and columns in grid

		- a list containing type:  ``[<class 'int'>]``
		- default list : ``[100, 99]``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``
		- min: ``1``
		- max: ``100000``


grid_span: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``particle_property_list``:  *<optional>*
		Description: - Create statistics for these named particle properties, list = ["water_depth"], for average of water depth at particle locations inside the counted regions

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``release_group_centered_grids`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``stats_gridded_time``

	* ``status_max`` :   ``[<class 'str'>]``   *<optional>*
		Description: Count only those particles with status  <= to this value

		- default: ``moving``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``status_min`` :   ``[<class 'str'>]``   *<optional>*
		Description: Count only those particles with status >= to this value

		- default: ``stationary``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between calculating statistics, wil be rounded to be a multiple of the particle tracking time step

		- default: ``3600.0``
		- units: ``sec``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``water_depth_max`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles in water depths less than this value

		- default: ``None``
		- min: ``0.0``

	* ``water_depth_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles in water depths greater than this value

		- default: ``None``
		- min: ``0.0``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write statistcs to disk

		- default: ``True``
		- possible_values: ``[True, False]``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position <= to this value

		- default: ``None``
		- units: ``meters above mean water level, so is < 0 at depth``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position >=  to this value

		- default: ``None``
		- units: ``meters above mean water level, so is < 0 at depth``


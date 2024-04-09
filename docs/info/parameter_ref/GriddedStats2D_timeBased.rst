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
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``coords_allowed_in_lat_lon_order`` :   ``<class 'bool'>``   *<optional>*
		Description: Allows points to be given (lat,lon) and order will be swapped before use, only used if hydro-model coords are in degrees

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``duration`` :   ``<class 'float'>``   *<optional>*
		Description: How long to do counting after start time, can be used instead of "end" parameter

		- default: ``None``
		- required_type: ``<class 'float'>``
		- min: ``0.0``
		- units: ``sec``
		- expert: ``False``

	* ``end`` :   ``iso8601date``   *<optional>*
		Description: Stop particle counting from this iso date-time, default is end of model run

		- default: ``None``
		- required_type: ``iso8601date``
		- expert: ``False``


grid_center: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``grid_size``:  *<optional>*
		Description: - number of rows and columns in grid

		- a list containing type:  ``[<class 'int'>]``
		- default list : ``[100, 99]``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``
		- min: ``1``
		- max: ``100000``
		- expert: ``False``


grid_span: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``particle_property_list``:  *<optional>*
		Description: - Create statistics for these named particle properties, list = ["water_depth"], for average of water depth at particle locations inside the counted regions

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``
		- expert: ``False``

	* ``release_group_centered_grids`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``stats_gridded_time``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``start`` :   ``iso8601date``   *<optional>*
		Description: Start particle counting from this date-time, default is start of model run

		- default: ``None``
		- required_type: ``iso8601date``
		- expert: ``False``

	* ``status_max`` :   ``[<class 'str'>]``   *<optional>*
		Description: Count only those particles with status  <= to this value

		- default: ``moving``
		- required_type: ``[<class 'str'>]``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- expert: ``False``

	* ``status_min`` :   ``[<class 'str'>]``   *<optional>*
		Description: Count only those particles with status >= to this value

		- default: ``stationary``
		- required_type: ``[<class 'str'>]``
		- possible_values: ``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'stationary', 'stranded_by_tide', 'on_bottom', 'moving']``
		- expert: ``False``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between calculating statistics, wil be rounded to be a multiple of the particle tracking time step

		- default: ``3600.0``
		- required_type: ``<class 'float'>``
		- units: ``sec``
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

	* ``water_depth_max`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles in water depths less than this value

		- default: ``None``
		- required_type: ``<class 'float'>``
		- min: ``0.0``
		- expert: ``False``

	* ``water_depth_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles in water depths greater than this value

		- default: ``None``
		- required_type: ``<class 'float'>``
		- min: ``0.0``
		- expert: ``False``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write statistcs to disk

		- default: ``True``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position <= to this value

		- default: ``None``
		- required_type: ``<class 'float'>``
		- units: ``meters above mean water level, so is < 0 at depth``
		- expert: ``False``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: Count only those particles with vertical position >=  to this value

		- default: ``None``
		- required_type: ``<class 'float'>``
		- units: ``meters above mean water level, so is < 0 at depth``
		- expert: ``False``



Expert Parameters:
*******************



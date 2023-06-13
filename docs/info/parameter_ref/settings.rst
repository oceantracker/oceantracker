#########
Settings
#########


Top level settings/parameters
______________________________



Parameters:
************

	* ``add_date_to_run_output_dir`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``advanced_settings``: nested parameter dictionary
		* ``max_warnings`` :   ``<class 'int'>``   *<optional>*
			- default: ``50``
			- min: ``0``

		* ``multiprocessing_case_start_delay`` :   ``<class 'float'>``   *<optional>*
			- default: ``None``
			- min: ``0.0``

		* ``numba_function_cache_size`` :   ``<class 'int'>``   *<optional>*
			- default: ``1024``
			- min: ``128``

		* ``profiler`` :   ``<class 'str'>``   *<optional>*
			Description: - Default oceantracker profiler, writes timings of decorated methods/functions to run/case_info file use of other profilers in development and requires additional installed modules

			- default: ``oceantracker``
			- possible_values: ``['none', 'oceantracker', 'cprofiler', 'line_profiler', 'scalene']``

		* ``use_random_seed`` :   ``<class 'bool'>``   *<optional>*
			Description: - Makes results reproducible, only use for testing developments give the same results!

			- default: ``False``
			- possible_values: ``[True, False]``

	* ``backtracking`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``block_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: - Block particles moving from wet to dry cells, ie. treat dry cells as if they are part of the lateral boundary

		- default: ``True``
		- possible_values: ``[True, False]``

	* ``case_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		Description: - insert this tag into output files name fore each case

		- default: ``None``

	* ``compact_mode`` :   ``<class 'bool'>``   *<optional>*
		Description: - Periodically discard dead particles from memory, eg. those too old to be be of interest, if used track output file also has a compact format

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``debug`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``max_run_duration`` :   ``<class 'float'>``   *<optional>*
		Description: - Maximum duration in seconds of model run, this sets a maximum, useful in testing

		- default: ``31536000000``
		- units: ``sec``

	* ``minimum_total_water_depth`` :   ``<class 'float'>``   *<optional>*
		Description: - Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering

		- default: ``0.25``
		- min: ``0.0``
		- units: ``m``

	* ``open_boundary_type`` :   ``<class 'int'>``   *<optional>*
		Description: - new- open boundary behaviour, only current option=1 is disable particle, only works if open boundary nodes  can be read or inferred from hydro-model, current schism using hgrid file, and inferred ROMS

		- default: ``0``
		- min: ``0``
		- max: ``1``

	* ``output_file_base`` :   ``<class 'str'>``   *<optional>*
		Description: - The start/base of all output files and name of sub-dir where output will be written

		- default: ``output_file_base``

	* ``particle_buffer_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``None``
		- min: ``1``

	* ``processors`` :   ``<class 'int'>``   *<optional>*
		Description: - number of processors used, if > 1 then cases in the case_list run in parallel

		- default: ``1``
		- min: ``1``

	* ``retain_culled_part_locations`` :   ``<class 'bool'>``   *<optional>*
		Description: - When particle marked dead/culled keep its position value, ie dont set position to nan so it does not appear in plots etc after death

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``root_output_dir`` :   ``<class 'str'>``   *<optional>*
		Description: - base dir for all output files

		- default: ``root_output_dir``

	* ``run_as_depth_averaged`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``screen_output_time_interval`` :   ``<class 'float'>``   *<optional>*
		Description: - Time in seconds between writing progress to the screen/log file

		- default: ``3600.0``

	* ``time_step`` :   ``<class 'float'>``   *<optional>*
		Description: - Time step in seconds for all cases

		- default: ``None``
		- min: ``0.01``
		- units: ``sec``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``No user note``

	* ``write_grid`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``write_output_files`` :   ``<class 'bool'>``   *<optional>*
		Description: - Set to False if no output files are to be written, eg. for output sent to web

		- default: ``True``
		- possible_values: ``[True, False]``

	* ``write_tracks`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``z0`` :   ``<class 'float'>``   *<optional>*
		Description: - Bottom roughness in meters, used for tolerance and log layer calcs.

		- default: ``0.005``
		- min: ``0.0001``
		- units: ``m``


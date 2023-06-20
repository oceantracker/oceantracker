#########
Settings
#########


Top level settings/parameters
______________________________



Parameters:
************

	* ``add_date_to_run_output_dir`` :   ``<class 'bool'>``   *<optional>*
		Description: Append the date to the output dir. name to help in keeping output from different runs separate

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``backtracking`` :   ``<class 'bool'>``   *<optional>*
		Description: Run model backwards in time

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``block_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: Block particles moving from wet to dry cells, ie. treat dry cells as if they are part of the lateral boundary

		- default: ``True``
		- possible_values: ``[True, False]``

	* ``case_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		Description: insert this tag into output files name for each case, for parallel runs this is set to C000, C001...

		- default: ``None``

	* ``debug`` :   ``<class 'bool'>``   *<optional>*
		Description: Gives more useful numba code error messages

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``max_particles`` :   ``<class 'int'>``   *<optional>*
		Description: Maximum number of particles to release, useful in testing

		- default: ``1000000000``
		- min: ``1``

	* ``max_run_duration`` :   ``<class 'float'>``   *<optional>*
		Description: Maximum duration in seconds of model run, this sets a maximum, useful in testing

		- default: ``31536000000``
		- units: ``sec``

	* ``max_warnings`` :   ``<class 'int'>``   *<optional>*
		Description: Number of warnings stored and written to output, useful in reducing file size when there are warnings at many time steps

		- default: ``50``
		- min: ``0``

	* ``minimum_total_water_depth`` :   ``<class 'float'>``   *<optional>*
		Description: Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering

		- default: ``0.25``
		- min: ``0.0``
		- units: ``m``

	* ``multiprocessing_case_start_delay`` :   ``<class 'float'>``   *<optional>*
		Description: Delay start of each case run parallel, to reduce congestion reading first hydo-model file

		- default: ``None``
		- min: ``0.0``

	* ``numba_function_cache_size`` :   ``<class 'int'>``   *<optional>*
		Description: Size of memory cache for compiled numba functions in kB?

		- default: ``2048``
		- min: ``128``

	* ``open_boundary_type`` :   ``<class 'int'>``   *<optional>*
		Description: new- open boundary behaviour, only current option=1 is disable particle, only works if open boundary nodes  can be read or inferred from hydro-model, current schism using hgrid file, and inferred ROMS

		- default: ``0``
		- min: ``0``
		- max: ``1``

	* ``output_file_base`` :   ``<class 'str'>``   *<optional>*
		Description: The start/base of all output files and name of sub-dir of "root_output_dir" where output will be written

		- default: ``output_file_base``

	* ``processors`` :   ``<class 'int'>``   *<optional>*
		Description: number of processors used, if > 1 then cases in the case_list run in parallel

		- default: ``None``
		- min: ``1``

	* ``profiler`` :   ``<class 'str'>``   *<optional>*
		Description: Default oceantracker profiler, writes timings of decorated methods/functions to run/case_info file use of other profilers in development and requires additional installed modules

		- default: ``oceantracker``
		- possible_values: ``['none', 'oceantracker', 'cprofiler', 'line_profiler', 'scalene']``

	* ``root_output_dir`` :   ``<class 'str'>``   *<optional>*
		Description: base dir for all output files

		- default: ``root_output_dir``

	* ``run_as_depth_averaged`` :   ``<class 'bool'>``   *<optional>*
		Description: in development; Force a run using 2D velocity  if available in files or  to allow 3D hydro-model to be depth averaged on the fly to run faster

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``screen_output_time_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between writing progress to the screen/log file

		- default: ``3600.0``

	* ``time_step`` :   ``<class 'float'>``   *<optional>*
		Description: Time step in seconds for all cases

		- default: ``None``
		- min: ``0.01``
		- units: ``sec``

	* ``use_random_seed`` :   ``<class 'bool'>``   *<optional>*
		Description: Makes results reproducible, only use for testing developments give the same results!

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		Description: Any run note to store in case info file

		- default: ``No user note``

	* ``write_output_files`` :   ``<class 'bool'>``   *<optional>*
		Description: Set to False if no output files are to be written, eg. for output sent to web

		- default: ``True``
		- possible_values: ``[True, False]``

	* ``write_tracks`` :   ``<class 'bool'>``   *<optional>*
		Description: Flag if "True" will write particle tracks to disk. For large runs and statistics done on the fly, is normally set to False to reduce output volumes

		- default: ``True``
		- possible_values: ``[True, False]``

	* ``z0`` :   ``<class 'float'>``   *<optional>*
		Description: Bottom roughness in meters, used for tolerance and log layer calcs.

		- default: ``0.005``
		- min: ``0.0001``
		- units: ``m``


##############
shared_params
##############



Parameters:
************

	* ``add_date_to_run_output_dir`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``backtracking`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``compact_mode`` :   ``<class 'bool'>``   *<optional>*
		Description: - Periodically discard dead particles from memory, eg. those too old to be be of interest, if used track output file also has a compact format

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``debug`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``max_duration`` :   ``timedelta``   *<optional>*
		Description: - Maximun duation in seconds to run all cases. Each case can have its own duration, this sets the maximum, useful in tsstingUseful

		- default: ``31536000000``

	* ``max_warnings`` :   ``<class 'int'>``   *<optional>*
		- default: ``50``
		- min: ``0``

	* ``minimum_total_water_depth`` :   ``<class 'float'>``   *<optional>*
		Description: - Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering

		- default: ``0.25``
		- min: ``0.0``

	* ``multiprocessing_case_start_delay`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``
		- min: ``0.0``

	* ``numba_function_cache_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``1024``
		- min: ``128``

	* ``output_file_base`` :   ``<class 'str'>``   *<optional>*
		Description: - The start/base of all output files and name of sub-dir where output will be written

		- default: ``default_output_file_base``

	* ``processors`` :   ``<class 'int'>``   *<optional>*
		Description: - number of processors used, if > 1 then cases in the case_list run in parallel

		- default: ``1``
		- min: ``1``

	* ``replicates`` :   ``<class 'int'>``   *<optional>*
		Description: - number of replicates of each case to run, allows running larger particle numbers for each case in less time if running in parallel

		- default: ``1``
		- min: ``1``

	* ``root_output_dir`` :   ``<class 'str'>``   *<optional>*
		Description: - base dir for all output files

		- default: ``default_root_output_dir``

	* ``screen_output_time_interval`` :   ``<class 'float'>``   *<optional>*
		Description: - Time in seconds between writing progress to the screen/log file

		- default: ``None``

	* ``shared_reader_memory`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``time_step`` :   ``<class 'float'>``   *<optional>*
		Description: - Time step in seconds for all cases

		- default: ``3600.0``
		- min: ``0.001``

	* ``use_numpy_random_seed`` :   ``<class 'bool'>``   *<optional>*
		Description: - Makes results reproducible, only use for testing developments give the same results!

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``No user note``

	* ``write_grid`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``write_output_files`` :   ``<class 'bool'>``   *<optional>*
		Description: - Set to False if no output files are to be written, eg. for output sent to web

		- default: ``True``
		- possible_values: ``[True, False]``


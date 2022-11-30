##############
shared_params
##############



.. warning::

	Lots more to add here and work on layout!!



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

	* ``max_duration`` :   ``<class 'float'>``   *<optional>*
		- default: ``1e+20``

	* ``max_warnings`` :   ``<class 'int'>``   *<optional>*
		- default: ``50``
		- min: ``0``

	* ``multiprocessing_case_start_delay`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``
		- min: ``0.0``

	* ``numba_function_cache_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``1024``
		- min: ``128``

	* ``output_file_base`` :   ``<class 'str'>``   *<optional>*
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
		- default: ``True``
		- possible_values: ``[True, False]``


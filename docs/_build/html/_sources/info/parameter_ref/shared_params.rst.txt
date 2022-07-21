##############
shared_params
##############



.. warning::

	Lots more to add here and work on layout!!


Parameters:
************

	* ``add_date_to_run_output_dir``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``backtracking``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``compact_mode``:  *<optional>*
		**Description:** - Periodically discard dead particles from memory, eg. those too old to be be of interest, if used track output file also has a compact format

		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``debug``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``max_duration``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``1e+20``

	* ``max_warnings``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``50``
		- min: ``0``

	* ``multiprocessing_case_start_delay``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``0.0``
		- min: ``0.0``

	* ``numba_function_cache_size``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``512``
		- min: ``128``

	* ``output_file_base``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``default_output_file_base``

	* ``processors``:  *<optional>*
		**Description:** - number of processors used, if > 1 then cases in the case_list run in parallel

		- type: ``<class 'int'>``
		- default: ``1``
		- min: ``1``

	* ``replicates``:  *<optional>*
		**Description:** - number of replicates of each case to run, allows running larger particle numbers for each case in less time if running in parallel

		- type: ``<class 'int'>``
		- default: ``1``
		- min: ``1``

	* ``root_output_dir``:  *<optional>*
		**Description:** - base dir for all ouput files

		- type: ``<class 'str'>``
		- default: ``default_root_output_dir``

	* ``use_numpy_random_seed``:  *<optional>*
		**Description:** - Makes results reproducible, only use for testing developments give the same results!

		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``No user note``

	* ``write_grid``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``write_output_files``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``


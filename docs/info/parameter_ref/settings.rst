#########
Settings
#########


Top level settings/parameters
______________________________


Parameters:
************

	* ``EPSG_code_metres_grid`` :   ``<class 'int'>``   *<optional>*
		Description: If hydro-model has lon_lat coords, then grid is converted to this meters system. For codes see https://epsg.io/. eg EPSG for NZ Transverse Mercator use 2193. Default grid is UTM

		- default: ``None``
		- data_type: ``<class 'int'>``

	* ``add_date_to_run_output_dir`` :   ``<class 'bool'>``   *<optional>*
		Description: Append the date to the output dir. name to help in keeping output from different runs separate

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``backtracking`` :   ``<class 'bool'>``   *<optional>*
		Description: Run model backwards in time

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``block_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: Block particles moving from wet to dry cells, ie. treat dry cells as if they are part of the lateral boundary

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``debug`` :   ``<class 'bool'>``   *<optional>*
		Description: more info on errors

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``display_grid_at_start`` :   ``<class 'bool'>``   *<optional>*
		Description: Pause during strat up to plot the grid for checking using matplotlib, clicking om image will print a coord

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``max_particles`` :   ``<class 'int'>``   *<optional>*
		Description: Maximum number of particles to release, useful to restrict if splitting particles

		- default: ``10000000000``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``max_run_duration`` :   ``<class 'float'>``   *<optional>*
		Description: Useful in testing setup with shorter runs, as normally run duration is determined from release groups. This  limits the maximum duration in seconds of model runs.

		- default: ``31536000000``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``1e-05``

	* ``max_warnings`` :   ``<class 'int'>``   *<optional>*
		Description: Number of warnings stored and written to output, useful in reducing file size when there are warnings at many time steps

		- default: ``50``
		- data_type: ``<class 'int'>``
		- min: ``0``

	* ``minimum_total_water_depth`` :   ``<class 'float'>``   *<optional>*
		Description: Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering

		- default: ``0.25``
		- data_type: ``<class 'float'>``
		- units: ``m``
		- min: ``0.0``

	* ``open_boundary_type`` :   ``<class 'int'>``   *<optional>*
		Description: new- open boundary behaviour, only current option=1 is disable particle, only works if open boundary nodes  can be read or inferred from hydro-model, current schism using hgrid file, and inferred ROMS

		- default: ``0``
		- data_type: ``<class 'int'>``
		- min: ``0``
		- max: ``1``

	* ``output_file_base`` :   ``<class 'str'>``   *<optional>*
		Description: The start/base of all output files and name of sub-dir of "root_output_dir" where output will be written

		- default: ``output_file_base``
		- data_type: ``<class 'str'>``

	* ``processors`` :   ``<class 'int'>``   *<optional>*
		Description: number of processors used, if > 1 then cases in the case_list to run in parallel

		- default: ``None``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``regrid_z_to_uniform_sigma_levels`` :   ``<class 'bool'>``   *<optional>*
		Description: much faster 3D runs by re-griding hydo-model fields in the z to uniform sigma levels on read, based on sigma most curve z_level profile. Some hydo-model are already uniform sigma, so this param is ignored, eg ROMS

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``root_output_dir`` :   ``<class 'str'>``   *<optional>*
		Description: base dir for all output files

		- default: ``root_output_dir``
		- data_type: ``<class 'str'>``

	* ``screen_output_time_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between writing progress to the screen/log file

		- default: ``3600.0``
		- data_type: ``<class 'float'>``

	* ``time_step`` :   ``<class 'float'>``   *<optional>*
		Description: Time step in seconds for all cases

		- default: ``3600.0``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``0.001``

	* ``use_A_Z_profile`` :   ``<class 'bool'>``   *<optional>*
		Description: Use the hydro-model vertical turbulent diffusivity profiles for vertical random walk (more realistic) instead of constant value (faster), if profiles are in the file

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``use_dispersion`` :   ``<class 'bool'>``   *<optional>*
		Description: Include random walk, allows it to be turned off if needed for applications like Lagrangian coherent structures

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``use_resuspension`` :   ``<class 'bool'>``   *<optional>*
		Description: Allow particles to resuspend

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		Description: Any run note to store in case info file

		- default: ``No user note``
		- data_type: ``<class 'str'>``

	* ``water_density`` :   ``<class 'float'>``   *<optional>*
		Description: Water density , default is seawater, an example of use is in calculating friction velocity from bottom stress,

		- default: ``1025.0``
		- data_type: ``<class 'float'>``
		- units: ``kg/m^3``
		- min: ``900.0``

	* ``write_dry_cell_flag`` :   ``<class 'bool'>``   *<optional>*
		Description: Write dry cell flag to all cells when writing particle tracks, which can be used to show dry cells on plots,may create large grid file, currently cannot be used with nested grids

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``write_tracks`` :   ``<class 'bool'>``   *<optional>*
		Description: Flag if "True" will write particle tracks to disk. For large runs and statistics done on the fly, is normally set to False to reduce output volumes

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``z0`` :   ``<class 'float'>``   *<optional>*
		Description: Bottom roughness, used for tolerance and log layer calcs.

		- default: ``0.005``
		- data_type: ``<class 'float'>``
		- units: ``m``
		- min: ``0.0001``


Expert Parameters:
*******************

	* ``NCDF_time_chunk`` :   ``<class 'int'>``   *<optional>*
		Description: Used when writing time series to netcdf output, is number of time steps per time chunk in the netcdf file

		- default: ``24``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``NUMBA_cache_code`` :   ``<class 'bool'>``   *<optional>*
		Description: Speeds start-up by caching complied Numba code on disk in root output dir. Can ignore warning/bug from numba "UserWarning: Inspection disabled for cached code..."

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``NUMBA_function_cache_size`` :   ``<class 'int'>``   *<optional>*
		Description: Size of memory cache for compiled numba functions in kB

		- default: ``4048``
		- data_type: ``<class 'int'>``
		- min: ``128``

	* ``dev_debug_opt`` :   ``<class 'int'>``   *<optional>*
		Description: does extra checks given by integer, not for general use

		- default: ``0``
		- data_type: ``<class 'int'>``

	* ``dev_debug_plots`` :   ``<class 'bool'>``   *<optional>*
		Description: show any debug plot generated at give dbug_level, not for general use

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``multi_processing_method`` :   ``<class 'str'>``   *<optional>*
		Description: How  multiprocessing is implemented, ie. sets  multiprocessing.set_start_method(str),  spawn= separate work spaces, fork = has copy on parents memory space

		- default: ``None``
		- data_type: ``<class 'str'>``
		- possible_values: ``['fork', 'spawn']``

	* ``multiprocessing_case_start_delay`` :   ``<class 'float'>``   *<optional>*
		Description: Delay start of each sucessive case run parallel, to reduce congestion reading first hydo-model file

		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- min: ``0.0``

	* ``particle_buffer_chunk_size`` :   ``<class 'int'>``   *<optional>*
		Description: How much particle property memory buffer sizes are increased by when they are full

		- default: ``500000``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``use_random_seed`` :   ``<class 'bool'>``   *<optional>*
		Description: Makes results reproducible, only use for testing developments give the same results!

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``


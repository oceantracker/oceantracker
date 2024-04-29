####################
CompactTracksWriter
####################

**Doc:** 

**short class_name:** CompactTracksWriter

**full class_name :** oceantracker.tracks_writer.track_writer_compact.CompactTracksWriter

**Inheritance:** > ParameterBaseClass> _BaseWriter> CompactTracksWriter


Parameters:
************

	* ``NCDF_particle_chunk`` :   ``<class 'int'>``   *<optional>*
		Description: number of particles per time chunk in the netcdf file

		- default: ``100000``
		- default: ``100000``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``100``

	* ``NCDF_time_chunk`` :   ``<class 'int'>``   *<optional>*
		Description: number of time steps per time chunk in the netcdf file

		- default: ``24``
		- default: ``24``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``1``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``retain_compact_files`` :   ``<class 'bool'>``   *<optional>*
		Description: keep  compact tracks files after conversion to rectangular format

		- default: ``False``
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``tracks_compact``
		- default: ``tracks_compact``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``time_steps_per_per_file`` :   ``<class 'int'>``   *<optional>*
		Description: Split track output into files with given number of time integer steps

		- default: ``None``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``1``

	* ``turn_off_write_particle_properties_list``:  *<optional>*
		Description: - Change default write param of particle properties to not write to tracks file, ie  tweak write flags individually

		- a list containing type:  ``[]``
		- default list : ``['water_velocity', 'particle_velocity', 'velocity_modifier']``
		- default: ``['water_velocity', 'particle_velocity', 'velocity_modifier']``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``turn_on_write_particle_properties_list``:  *<optional>*
		Description: - Change default write param of particle properties to write to tracks file, ie  tweak write flags individually

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: the time in model seconds between writes (will be rounded to model time step)

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- units: ``sec``
		- min: ``0.01``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``write_dry_cell_flag`` :   ``<class 'bool'>``   *<optional>*
		Description: Write dry cell flag to track output file for all cells, which can be used to show dry cells on plots, off by default to keep file size down

		- default: ``False``
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``



Expert Parameters:
*******************



####################
CompactTracksWriter
####################

**Description:** 

**Class:** oceantracker.tracks_writer.track_writer_compact.CompactTracksWriter

**File:** oceantracker/tracks_writer/track_writer_compact.py

**Inheritance:** _BaseWriter> CompactTracksWriter


Parameters:
************

	* ``NCDF_particle_chunk`` :   ``<class 'int'>``   *<optional>*
		Description: - number of particles per time chunk in the netcdf file

		- default: ``100000``
		- min: ``1000``

	* ``NCDF_time_chunk`` :   ``<class 'int'>``   *<optional>*
		Description: - number of time steps per time chunk in the netcdf file

		- default: ``24``
		- min: ``1``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``convert`` :   ``<class 'bool'>``   *<optional>*
		Description: - convert compact tracks file to rectangular for at end of the run

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``requires_3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``retain_compact_files`` :   ``<class 'bool'>``   *<optional>*
		Description: - keep  compact tracks files after conversion to rectangular format

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``tracks_compact``

	* ``time_steps_per_per_file`` :   ``<class 'int'>``   *<optional>*
		Description: - Split track output into files with given number of time integer steps

		- default: ``None``
		- min: ``1``

	* ``turn_off_write_particle_properties_list``:  *<optional>*
		Description: - Change default write param of particle properties to not write to tracks file, ie  tweak write flags individually

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['water_velocity', 'particle_velocity', 'velocity_modifier']``
		- can_be_empty_list: ``True``

	* ``turn_on_write_particle_properties_list``:  *<optional>*
		Description: - Change default write param of particle properties to write to tracks file, ie  tweak write flags individually

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``

	* ``update_interval`` :   ``<class 'int'>``   *<optional>*
		Description: - the time in model seconds between writes (will be rounded to model time step)

		- default: ``None``
		- min: ``1``
		- units: ``sec``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write_dry_cell_index`` :   ``<class 'bool'>``   *<optional>*
		Description: - Write dry cell flag to track output file for all cells, which can be used to show dry cells on plots

		- default: ``True``
		- possible_values: ``[True, False]``


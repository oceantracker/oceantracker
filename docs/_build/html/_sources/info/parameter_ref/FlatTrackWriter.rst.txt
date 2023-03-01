################
FlatTrackWriter
################

**Description:** 

**Class:** oceantracker.tracks_writer.track_writer_compact.FlatTrackWriter

**File:** oceantracker/tracks_writer/track_writer_compact.py

**Inheritance:** _BaseWriter> RectangularTrackWriter> FlatTrackWriter

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``NCDF_time_chunk`` :   ``<class 'int'>``   *<optional>*
		- default: ``24``
		- min: ``1``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- default: ``None``

	* ``output_step_count`` :   ``<class 'int'>``   *<optional>*
		Description: - Write track data every output_step_count steps of the model

		- default: ``1``
		- min: ``1``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``tracks``

	* ``time_steps_per_per_file`` :   ``<class 'int'>``   *<optional>*
		Description: - Split track output into files with given number of time steps

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

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write_dry_cell_index`` :   ``<class 'bool'>``   *<optional>*
		Description: - Write dry cell flag to track output file for all cells, which can be used to show dry cells on plots

		- default: ``True``
		- possible_values: ``[True, False]``


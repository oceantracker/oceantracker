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

	* ``NCDF_time_chunk``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``24``
		- min: ``1``

	* ``case_output_file_tag``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``tracks``

	* ``class_name``:  *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``description``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``name``:  *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- type: ``<class 'str'>``
		- default: ``None``

	* ``output_step_count``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``1``
		- min: ``1``

	* ``turn_off_write_particle_properties_list``:  *<optional>*
		- a list containing type:  ``<class 'str'>``
		- default list item: ``None``
		- can_be_empty_list: ``True``

	* ``turn_on_write_particle_properties_list``:  *<optional>*
		- a list containing type:  ``<class 'str'>``
		- default list item: ``None``
		- can_be_empty_list: ``True``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


#######################
LogPolygonEntryAndExit
#######################

**Description:** 

**Class:** oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit

**File:** oceantracker/event_loggers/log_polygon_entry_and_exit.py

**Inheritance:** _BaseEventLogger> LogPolygonEntryAndExit

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``case_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``inside_polygon_events``

	* ``chunk_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``5000``
		- min: ``1``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- default: ``None``

	* ``particle_prop_to_write_list``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['ID', 'x', 'IDpulse', 'IDrelease_group', 'user_release_group_ID', 'status', 'age']``
		- can_be_empty_list: ``True``

	* ``polygon_list``:  *<optional>*

polygon_list: still working on display  of lists of dict, eg nested polygon list 

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


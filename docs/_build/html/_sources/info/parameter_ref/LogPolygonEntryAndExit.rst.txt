#######################
LogPolygonEntryAndExit
#######################

**Description:** 

**full class_name :** oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit

**short class_name:** LogPolygonEntryAndExit

docs>>

**Inheritance:** > ParameterBaseClass> _BaseEventLogger> LogPolygonEntryAndExit


Parameters:
************

	* ``chunk_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``500000``
		- min: ``1``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``particle_prop_to_write_list``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['ID', 'x', 'IDpulse', 'IDrelease_group', 'user_release_groupID', 'status', 'age']``
		- can_be_empty_list: ``True``

	* ``polygon_list``:  *<optional>*

polygon_list: still working on display  of lists of dict, eg nested polygon list 

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``inside_polygon_events``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


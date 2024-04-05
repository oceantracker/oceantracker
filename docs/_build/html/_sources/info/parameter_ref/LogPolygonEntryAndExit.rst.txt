#######################
LogPolygonEntryAndExit
#######################

**Doc:** 

**short class_name:** LogPolygonEntryAndExit

**full class_name :** oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit

**Inheritance:** > ParameterBaseClass> _BaseEventLogger> LogPolygonEntryAndExit


Parameters:
************

	* ``chunk_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``500000``
		- required_type: ``<class 'int'>``
		- min: ``1``
		- expert: ``False``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``particle_prop_to_write_list``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['ID', 'x', 'IDpulse', 'IDrelease_group', 'user_release_groupID', 'status', 'age']``
		- can_be_empty_list: ``True``
		- expert: ``False``

	* ``polygon_list``:  *<optional>*

polygon_list: still working on display  of lists of dict, eg nested polygon list 

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``inside_polygon_events``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``
		- required_type: ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``
		- expert: ``False``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- required_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``
		- expert: ``False``



Expert Parameters:
*******************



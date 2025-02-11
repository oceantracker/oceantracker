################
BaseEventLogger
################

**Doc:** 

**short class_name:** BaseEventLogger

**full class_name :** oceantracker.event_loggers._base_event_loggers.BaseEventLogger

**Inheritance:** > ParameterBaseClass> BaseEventLogger


Parameters:
************

	* ``chunk_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``500000``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``particle_prop_to_write_list``:  *<optional>*
		- a list containing type:  ``[]``
		- default list : ``['ID', 'x', 'IDpulse', 'IDrelease_group', 'user_release_groupID', 'status', 'age']``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``event_logger``
		- data_type: ``<class 'str'>``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



Expert Parameters:
*******************



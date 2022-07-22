################
BaseEventLogger
################

**Class:** oceantracker.event_loggers._base_event_loggers.BaseEventLogger

**File:** oceantracker/event_loggers/_base_event_loggers.py

**Inheritance:** BaseEventLogger

**Default internal name:** ``"not given in defaults"``

**Description:** 


Parameters:
************

	* ``case_output_file_tag``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``event_logger``

	* ``chunk_size``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``5000``
		- min: ``1``

	* ``class_name``:  *<optional>*
		**Description:** - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``doc_str``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``name``:  *<optional>*
		**Description:** - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- type: ``<class 'str'>``
		- default: ``None``

	* ``particle_prop_to_write_list``:  *<optional>*
		- a list containing type:  ``<class 'str'>``
		- default list item: ``None``
		- self: ``<oceantracker.util.parameter_checking.ParameterListChecker object at 0x0000023DDBA59F40>``
		- can_be_empty_list: ``True``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``write``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``


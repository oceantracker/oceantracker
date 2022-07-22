###########
BaseReader
###########

**Class:** oceantracker.reader._base_reader.BaseReader

**File:** oceantracker/reader/_base_reader.py

**Inheritance:** BaseReader

**Default internal name:** ``"not given in defaults"``

**Description:** 


Parameters:
************

	* ``class_name``:  *<optional>*
		**Description:** - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``cords_in_lat_long``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``depth_average``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``


dimension_map: still working on display  of nested  params dict <class 'dict'>

	* ``doc_str``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


field_variables: still working on display  of nested  params dict <class 'dict'>

	* ``field_variables_to_depth_average``:  *<optional>*
		- a list containing type:  ``<class 'str'>``
		- default list item: ``None``
		- self: ``<oceantracker.util.parameter_checking.ParameterListChecker object at 0x0000023DDB46BF40>``
		- can_be_empty_list: ``True``

	**<isrequired>**
		- type: ``<class 'str'>``
		- default: ``None``


grid_variables: still working on display  of nested  params dict <class 'dict'>

	* ``input_dir``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``isodate_of_hindcast_time_zero``:  *<optional>*
		- type: ``iso8601date``
		- default: ``1970-01-01``

	* ``max_numb_files_to_load``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``10000000``
		- min: ``1``

	* ``minimum_total_water_depth``:  *<optional>*
		**Description:** - Min. water depth used to decide if stranded by tide and which are dry cells to block particles from entering

		- type: ``<class 'float'>``
		- default: ``0.25``
		- min: ``0.0``

	* ``name``:  *<optional>*
		**Description:** - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- type: ``<class 'str'>``
		- default: ``None``

	* ``search_sub_dirs``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``time_buffer_size``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``48``
		- min: ``2``

	* ``time_zone``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``None``
		- min: ``-12``
		- max: ``23``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


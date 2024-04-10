############################
dev_GenericStructuredReader
############################

**Doc:** 

**short class_name:** dev_GenericStructuredReader

**full class_name :** oceantracker.reader.generic_stuctured_reader.dev_GenericStructuredReader


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseReader> _BaseGenericReader> dev_GenericStructuredReader


Parameters:
************

	* ``EPSG`` :   ``<class 'int'>``   *<optional>*
		Description: integer code for coordinate transform of hydro-model, only used if running in  lon-lat mode and code not in hindcast, eg. EPSG for New Zealand Transverse Mercator 2000 = 2193, find codes at https://spatialreference.org/

		- default: ``None``
		- required_type: ``<class 'int'>``
		- expert: ``False``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``field_variables``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``
		- obsolete: `` parameter obsolete, use "load_fields" parameter, with field_variable_map if needed``
		- expert: ``False``

	* ``file_mask`` :   ``<class 'str'>`` **<isrequired>**
		Description: Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``hydro_model_cords_in_lat_long`` :   ``<class 'bool'>``   *<optional>*
		Description: Force conversion given nodal lat longs to a UTM metres grid, only used if lat long coordinates not auto detected

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``input_dir`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``isodate_of_hindcast_time_zero`` :   ``iso8601date``   *<optional>*
		Description: use to offset times to required times zone

		- default: ``None``
		- required_type: ``iso8601date``
		- expert: ``False``

	* ``load_fields``:  *<optional>*
		Description: - A list of names of any additional variables to read and interplolate to give particle values, eg. a concentration field (water_veloctiy, tide and water_depth fields are always loaded). If a given name is in field_variable_map, then the mapped file variables will be used internally and in output. If not the given file variable name will be used internally and in particle property output. For any additional vector fields user must supply a file variable map in the "field_variable_map" parameter

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``
		- expert: ``False``

	* ``max_numb_files_to_load`` :   ``<class 'int'>``   *<optional>*
		Description: Only read no more than this number of hindcast files, useful when setting up to speed run

		- default: ``10000000``
		- required_type: ``<class 'int'>``
		- min: ``1``
		- expert: ``False``

	* ``one_based_indices`` :   ``<class 'bool'>``   *<optional>*
		Description: indices in hindcast start at 1, not zero, eg. triangulation nodes start at 1 not zero as in python

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``time_buffer_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``24``
		- required_type: ``<class 'int'>``
		- min: ``2``
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

	* ``vertical_regrid`` :   ``<class 'bool'>``   *<optional>*
		Description: Convert vertical grid to same sigma levels across domain

		- default: ``True``
		- required_type: ``<class 'bool'>``
		- expert: ``False``



Expert Parameters:
*******************



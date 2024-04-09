############
dev_DELFTFM
############

**Doc:** 

**short class_name:** dev_DELFTFM

**full class_name :** oceantracker.reader.delft_fm.dev_DELFTFM


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseReader> dev_DELFTFM


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


dev_test: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterTimeChecker'>

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

	* ``load_fields``:  *<optional>*
		Description: - always load tide and water depth, for dry cells id 2D

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['water_depth']``
		- can_be_empty_list: ``True``
		- expert: ``False``

	* ``max_numb_files_to_load`` :   ``<class 'int'>``   *<optional>*
		Description: Only read no more than this number of hindcast files, useful when setting up to speed run

		- default: ``10000000``
		- required_type: ``<class 'int'>``
		- min: ``1``
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



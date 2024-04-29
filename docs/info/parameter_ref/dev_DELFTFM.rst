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
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``field_variables``:  *<optional>*
		Description: - parameter obsolete, use "load_fields" parameter, with field_variable_map if needed

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``True``
		- possible_types: ``[]``
		- make_list_unique: ``True``
		- min_len: ``0``

	* ``file_mask`` :   ``<class 'str'>`` **<isrequired>**
		Description: Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern

		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``hydro_model_cords_in_lat_long`` :   ``<class 'bool'>``   *<optional>*
		Description: Force conversion given nodal lat longs to a UTM metres grid, only used if lat long coordinates not auto detected

		- default: ``False``
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``

	* ``input_dir`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``load_fields``:  *<optional>*
		Description: - always load tide and water depth, for dry cells id 2D

		- a list containing type:  ``[]``
		- default list : ``['water_depth']``
		- default: ``['water_depth']``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``max_numb_files_to_load`` :   ``<class 'int'>``   *<optional>*
		Description: Only read no more than this number of hindcast files, useful when setting up to speed run

		- default: ``10000000``
		- default: ``10000000``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``1``

	* ``time_buffer_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``24``
		- default: ``24``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``2``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``vertical_regrid`` :   ``<class 'bool'>``   *<optional>*
		Description: Convert vertical grid to same sigma levels across domain

		- default: ``True``
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``



Expert Parameters:
*******************



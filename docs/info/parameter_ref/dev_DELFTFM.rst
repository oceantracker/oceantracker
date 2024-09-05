############
dev_DELFTFM
############

**Doc:** 

**short class_name:** dev_DELFTFM

**full class_name :** oceantracker.reader.delft_fm.dev_DELFTFM


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseReader> _BaseUnstructuredReader> dev_DELFTFM


Parameters:
************

	* ``EPSG`` :   ``<class 'int'>``   *<optional>*
		Description: integer code for coordinate transform of hydro-model, only used if running in  lon-lat mode and code not in hindcast, eg. EPSG for New Zealand Transverse Mercator 2000 = 2193, find codes at https://spatialreference.org/

		- default: ``None``
		- data_type: ``<class 'int'>``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``file_mask`` :   ``<class 'str'>`` **<isrequired>**
		Description: Mask for file names, eg "scout*.nc", finds all files matching in  "input_dir" and its sub dirs that match the file_mask pattern

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``hydro_model_cords_in_lat_long`` :   ``<class 'bool'>``   *<optional>*
		Description: Force conversion given nodal lat longs to a UTM metres grid, only used if lat long coordinates not auto detected

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``input_dir`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``load_fields``:  *<optional>*
		Description: - always load tide and water depth, for dry cells id 2D

		- a list containing type:  ``[]``
		- default list : ``['water_depth']``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``max_numb_files_to_load`` :   ``<class 'int'>``   *<optional>*
		Description: Only read no more than this number of hindcast files, useful when setting up to speed run

		- default: ``10000000``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``one_based_indices`` :   ``<class 'bool'>``   *<optional>*
		Description: DELFT 3D has indices starting at 1 not zero

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``time_buffer_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``24``
		- data_type: ``<class 'int'>``
		- min: ``2``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``variable_signature``:  *<optional>*
		Description: - Variable names used to test if file is this format

		- a list containing type:  ``[]``
		- default list : ``['mesh2d_waterdepth', 'mesh2d_face_nodes']``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``vertical_regrid`` :   ``<class 'bool'>``   *<optional>*
		Description: Convert vertical grid to same sigma levels across domain

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



Expert Parameters:
*******************

	* ``development`` :   ``<class 'bool'>``   *<optional>*
		Description: Class is under development and testing

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



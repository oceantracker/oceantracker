###############
DELF3DFMreader
###############

**Doc:** 

**short class_name:** DELF3DFMreader

**full class_name :** oceantracker.reader.DEFT3DFM_reader.DELF3DFMreader


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseReader> _BaseUnstructuredReader> DELF3DFMreader


Parameters:
************

	* ``EPSG_code`` :   ``<class 'int'>``   *<optional>*
		Description: integer code for coordinate transform of hydro-model, only used if setting "use_geographic_coords"= True and hindcast not in geographic coords, EPSG for New Zealand Transverse Mercator 2000 = 2193, find codes at https://spatialreference.org/

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

	* ``drop_variables``:  *<optional>*
		Description: - List of problematic file variable names to ignore, eg non-critcal variables not present in all files/all times

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``True``
		- min_len: ``0``

	* ``geographic_coords`` :   ``<class 'bool'>``   *<optional>*
		Description: Read file coords as geographic values,normaly auto-detects if in geographic coords, using this setting  forces reading as geograraphic coord if auto-dectect fails

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



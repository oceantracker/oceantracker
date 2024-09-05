###################
SCHISMreaderNCDFv5
###################

**Doc:** 

**short class_name:** SCHISMreaderNCDFv5

**full class_name :** oceantracker.reader.SCHISM_reader_v5.SCHISMreaderNCDFv5

**Inheritance:** > ParameterBaseClass> _BaseReader> _BaseUnstructuredReader> SCHISMreaderNCDF> SCHISMreaderNCDFv5


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

	* ``hgrid_file_name`` :   ``<class 'str'>``   *<optional>*
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
		Description: - A list of names of any additional variables to read and interplolate to give particle values, eg. a concentration field (water_veloctiy, tide and water_depth fields are always loaded). If a given name is in field_variable_map, then the mapped file variables will be used internally and in output. If not the given file variable name will be used internally and in particle property output. For any additional vector fields user must supply a file variable map in the "field_variable_map" parameter

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``True``
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
		Description: Schism has indices starting at 1 not zero

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
		- default list : ``['SCHISM_hgrid_node_x', 'horizontalVelX', 'dryFlagElement']``
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



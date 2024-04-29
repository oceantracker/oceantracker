###################
SCHISMreaderNCDFv5
###################

**Doc:** 

**short class_name:** SCHISMreaderNCDFv5

**full class_name :** oceantracker.reader.schism_reader_v5.SCHISMreaderNCDFv5

**Inheritance:** > ParameterBaseClass> _BaseReader> SCHISMreaderNCDF> SCHISMreaderNCDFv5


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

	* ``hgrid_file_name`` :   ``<class 'str'>``   *<optional>*
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
		Description: - A list of names of any additional variables to read and interplolate to give particle values, eg. a concentration field (water_veloctiy, tide and water_depth fields are always loaded). If a given name is in field_variable_map, then the mapped file variables will be used internally and in output. If not the given file variable name will be used internally and in particle property output. For any additional vector fields user must supply a file variable map in the "field_variable_map" parameter

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_types: ``[]``
		- make_list_unique: ``True``
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



##########################
GenericUnstructuredReader
##########################

**Doc:** 

**short class_name:** GenericUnstructuredReader

**full class_name :** oceantracker.reader.dev_generic_reader.GenericUnstructuredReader


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseReader> _BaseUnstructuredReader> _BaseGenericReader> GenericUnstructuredReader


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

	* ``isodate_of_hindcast_time_zero`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']`` **<isrequired>**
		Description: use to offset times to required times zone

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

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

	* ``one_based_indices`` :   ``<class 'bool'>`` **<isrequired>**
		Description: indices in hindcast start at 1, not zero, eg. triangulation nodes start at 1 not zero as in python

		- default: ``None``
		- data_type: ``<class 'bool'>``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``vertical_grid_type`` :   ``<class 'str'>`` **<isrequired>**
		Description: use to offset times to required times zone

		- default: ``None``
		- data_type: ``<class 'str'>``
		- possible_values: ``['Slayer', 'LSC', 'Sigma', 'Zfixed']``

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



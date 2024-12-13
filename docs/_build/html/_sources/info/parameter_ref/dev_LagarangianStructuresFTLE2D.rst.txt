################################
dev_LagarangianStructuresFTLE2D
################################

**Doc:** Time series of Lagrangian Coherent Structures heat maps,     calculated as Finite-Time Lyapunov exponents (FTLEs) at given lag times,     see Haller, G., 2015. Lagrangian coherent structures.     Annual review of fluid mechanics, 47, pp.137-162.')     Currently only 2D  implemented     

**short class_name:** dev_LagarangianStructuresFTLE2D

**full class_name :** oceantracker.integrated_model.lagraingian_structures_FTLE_2D.dev_LagarangianStructuresFTLE2D


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseIntegratedModel> dev_LagarangianStructuresFTLE2D


Parameters:
************

	* ``backwards`` :   ``<class 'bool'>``   *<optional>*
		Description: Do LCS backwards in time

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``end`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: end date of LSC releases. Model should run max(lags) beyond this send date to calculate LSC for last pulse of grid release.  Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``floating`` :   ``<class 'bool'>``   *<optional>*
		Description: Do LCS for floating partyicles, in development currently only option

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``


grid_center: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``grid_size``:  *<optional>*
		Description: - number of rows and columns in grid

		- a list containing type:  ``[]``
		- default list : ``[100, 99]``
		- data_type: ``<class 'int'>``
		- min: ``1``
		- max: ``100000``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- fixed_len: ``2``
		- min_len: ``0``


grid_span: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``lags``:**<isrequired>**
		Description: - List of one or more times after each pulse is released to calculate LCS.

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``1``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``1``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``output_file_tag`` :   ``<class 'str'>``   *<optional>*
		Description: tag on output file

		- default: ``LCS``
		- data_type: ``<class 'str'>``

	* ``release_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between grid releases of pulses of particles. For each pulse an LCS will be calculated at the given lag times. This creates a LCS time series for each lag at this time interval

		- default: ``3600.0``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``0.0``

	* ``start`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: start date of LSC releases, Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``write_intermediate_results`` :   ``<class 'bool'>``   *<optional>*
		Description: write intermediate arrays, x_lag, strain_matrix. Useful for checking results

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``write_tracks`` :   ``<class 'bool'>``   *<optional>*
		Description: Flag if "True" will write particle tracks to disk. This is off by default for LCS

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: Only allow particles to be below this vertical position

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``meters above mean water level, so is < 0 at depth``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: Only allow particles to be above this vertical position

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``meters above mean water level, so is < 0 at depth``



Expert Parameters:
*******************



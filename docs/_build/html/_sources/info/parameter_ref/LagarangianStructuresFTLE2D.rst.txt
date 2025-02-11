############################
LagarangianStructuresFTLE2D
############################

**Description:** 

**full class_name :** oceantracker.integrated_model.lagraingian_structures_FTLE_2D.LagarangianStructuresFTLE2D

**short class_name:** LagarangianStructuresFTLE2D

Time series of Lagrangian Coherent Structures heat maps,
     calculated as Finite-Time Lyapunov exponents (FTLEs) at given lag times,
     see Haller, G., 2015. Lagrangian coherent structures.
     Annual review of fluid mechanics, 47, pp.137-162.')
     Currently only 2D  implemented

**Inheritance:** > ParameterBaseClass> _BaseModel> LagarangianStructuresFTLE2D


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``end`` :   ``iso8601date``   *<optional>*
		Description: end date of LSC calculation, Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``

	* ``floating`` :   ``<class 'bool'>``   *<optional>*
		Description: Particles will float at free surface if a 3D model

		- default: ``True``
		- possible_values: ``[True, False]``


grid_center: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``grid_size``:  *<optional>*
		Description: - number of rows and columns in grid

		- a list containing type:  ``[<class 'int'>]``
		- default list : ``[100, 99]``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``
		- min: ``1``
		- max: ``100000``


grid_span: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``lags``:  *<optional>*
		Description: - List of one or more times after particle release to calculate Lagarangian Coherent Structures, default is 1 day

		- a list containing type:  ``[<class 'float'>, <class 'int'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- units: ``sec``
		- min: ``1``

	* ``output_file_tag`` :   ``<class 'str'>``   *<optional>*
		Description: tag on output file

		- default: ``LCS``

	* ``start`` :   ``iso8601date``   *<optional>*
		Description: start date of LSC calculation, Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between calculating statistics, will be rounded to be a multiple of the particle tracking time step

		- default: ``3600.0``
		- units: ``sec``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write_intermediate_results`` :   ``<class 'bool'>``   *<optional>*
		Description: write intermediate arrays, x_lag, strain_matrix. Useful for checking results

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``write_tracks`` :   ``<class 'bool'>``   *<optional>*
		Description: Flag if "True" will write particle tracks to disk. This is off by default for LCS

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: Only allow particles to be below this vertical position

		- default: ``None``
		- units: ``meters above mean water level, so is < 0 at depth``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: Only allow particles to be above this vertical position

		- default: ``None``
		- units: ``meters above mean water level, so is < 0 at depth``


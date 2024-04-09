################################
dev_LagarangianStructuresFTLE2D
################################

**Doc:** Time series of Lagrangian Coherent Structures heat maps,     calculated as Finite-Time Lyapunov exponents (FTLEs) at given lag times,     see Haller, G., 2015. Lagrangian coherent structures.     Annual review of fluid mechanics, 47, pp.137-162.')     Currently only 2D  implemented     

**short class_name:** dev_LagarangianStructuresFTLE2D

**full class_name :** oceantracker.integrated_model.lagraingian_structures_FTLE_2D.dev_LagarangianStructuresFTLE2D


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseModel> dev_LagarangianStructuresFTLE2D


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``end`` :   ``iso8601date``   *<optional>*
		Description: end date of LSC calculation, Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``
		- required_type: ``iso8601date``
		- expert: ``False``

	* ``floating`` :   ``<class 'bool'>``   *<optional>*
		Description: Particles will float at free surface if a 3D model

		- default: ``True``
		- required_type: ``<class 'bool'>``
		- expert: ``False``


grid_center: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``grid_size``:  *<optional>*
		Description: - number of rows and columns in grid

		- a list containing type:  ``[<class 'int'>]``
		- default list : ``[100, 99]``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``
		- min: ``1``
		- max: ``100000``
		- expert: ``False``


grid_span: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``lags``:**<isrequired>**
		Description: - List of one or more times after particle release to calculate Lagarangian Coherent Structures, default is 1 day

		- a list containing type:  ``[<class 'float'>, <class 'int'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- min_length: ``1``
		- units: ``sec``
		- min: ``1``
		- expert: ``False``

	* ``output_file_tag`` :   ``<class 'str'>``   *<optional>*
		Description: tag on output file

		- default: ``LCS``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``start`` :   ``iso8601date``   *<optional>*
		Description: start date of LSC calculation, Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``
		- required_type: ``iso8601date``
		- expert: ``False``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds between calculating statistics, will be rounded to be a multiple of the particle tracking time step

		- default: ``3600.0``
		- required_type: ``<class 'float'>``
		- min: ``0.0``
		- units: ``sec``
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

	* ``write_intermediate_results`` :   ``<class 'bool'>``   *<optional>*
		Description: write intermediate arrays, x_lag, strain_matrix. Useful for checking results

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``write_tracks`` :   ``<class 'bool'>``   *<optional>*
		Description: Flag if "True" will write particle tracks to disk. This is off by default for LCS

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: Only allow particles to be below this vertical position

		- default: ``None``
		- required_type: ``<class 'float'>``
		- units: ``meters above mean water level, so is < 0 at depth``
		- expert: ``False``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: Only allow particles to be above this vertical position

		- default: ``None``
		- required_type: ``<class 'float'>``
		- units: ``meters above mean water level, so is < 0 at depth``
		- expert: ``False``



Expert Parameters:
*******************



#####################
InterpTriangularGrid
#####################

**Doc:** 

**short class_name:** InterpTriangularGrid

**full class_name :** oceantracker.interpolator.interp_triangle_native_grid.InterpTriangularGrid

**Inheritance:** > ParameterBaseClass> _BaseInterp> InterpTriangularGrid


Parameters:
************

	* ``bc_walk_tol`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0001``
		- data_type: ``<class 'float'>``
		- min: ``0.0``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``debug_check_cell`` :   ``<class 'bool'>``   *<optional>*
		Description: checks particles are inside the cell found by interp

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``max_search_steps`` :   ``<class 'int'>``   *<optional>*
		- default: ``500``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``



Expert Parameters:
*******************

	* ``development`` :   ``<class 'bool'>``   *<optional>*
		Description: Class is under development and testing

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



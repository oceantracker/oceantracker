#######
Solver
#######

**Doc:**  Does particle tracking solution 

**short class_name:** Solver

**full class_name :** oceantracker.solver.solver.Solver

**Inheritance:** > ParameterBaseClass> Solver


Parameters:
************

	* ``RK_order`` :   ``<class 'int'>``   *<optional>*
		- default: ``4``
		- data_type: ``<class 'int'>``
		- possible_values: ``[1, 2, 4]``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

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



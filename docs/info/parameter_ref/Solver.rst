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
		- required_type: ``<class 'int'>``
		- possible_values: ``[1, 2, 4]``
		- expert: ``False``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
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



Expert Parameters:
*******************



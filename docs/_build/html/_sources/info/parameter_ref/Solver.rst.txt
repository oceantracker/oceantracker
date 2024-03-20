#######
Solver
#######

**Description:** 

**class_name:** oceantracker.solver.solver.Solver

**File:** oceantracker/solver/solver.py

**Inheritance:** Solver


Parameters:
************

	* ``RK_order`` :   ``<class 'int'>``   *<optional>*
		- default: ``4``
		- possible_values: ``[1, 2, 4]``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


##################
BasicResuspension
##################

**Description:** 

**class_name:** oceantracker.resuspension.resuspension.BasicResuspension

**File:** oceantracker/resuspension/resuspension.py

**Inheritance:** _BaseResuspension> BasicResuspension


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``critical_friction_velocity`` :   ``<class 'float'>``   *<optional>*
		Description: Critical friction velocity, u_* in m/s defined in terms of bottom stress (this param is not the same as near seabed velocity)

		- default: ``0.0``
		- min: ``0.0``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


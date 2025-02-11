##################
BasicResuspension
##################

**Doc:** 

**short class_name:** BasicResuspension

**full class_name :** oceantracker.resuspension.resuspension.BasicResuspension

**Inheritance:** > ParameterBaseClass> BaseResuspension> BasicResuspension


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``critical_friction_velocity`` :   ``<class 'float'>``   *<optional>*
		Description: Critical friction velocity, u_* in m/s defined in terms of bottom stress (this param is not the same as near seabed velocity)

		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- min: ``0.0``

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



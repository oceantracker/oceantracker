##################
BasicResuspension
##################

**Description:** 

**Class:** oceantracker.resuspension.resuspension.BasicResuspension

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

	* ``friction_velocity_field_class_name`` :   ``<class 'str'>``   *<optional>*
		- default: ``oceantracker.fields.friction_velocity.FrictionVelocity``

	* ``requires_3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


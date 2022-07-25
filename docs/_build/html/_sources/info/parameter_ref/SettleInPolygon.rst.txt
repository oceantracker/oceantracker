################
SettleInPolygon
################

**Description:** 

**Class:** oceantracker.trajectory_modifiers.settle_in_polygon.SettleInPolygon

**File:** oceantracker/trajectory_modifiers/settle_in_polygon.py

**Inheritance:** _BaseTrajectoryModifier> SettleInPolygon

**Default internal name:** ``"settle_in_polygon"``


Parameters:
************

	* ``class_name``:  *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``description``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``name``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``settle_in_polygon``

	* ``polygon``: nested parameter dictionary
		* ``points``:**<isrequired>**
			- type: ``vector``
			- default: ``None``

	* ``probability_of_settlement``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``0.0``

	* ``requires_3D``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``settlement_duration``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``0.0``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


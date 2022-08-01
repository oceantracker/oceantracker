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

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		- default: ``settle_in_polygon``

	* ``polygon``: nested parameter dictionary
		* ``points`` :   ``vector`` **<isrequired>**
			- default: ``None``

	* ``probability_of_settlement`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``

	* ``requires_3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``settlement_duration`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


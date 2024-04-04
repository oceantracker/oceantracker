################
SettleInPolygon
################

**Description:** 

**full class_name :** oceantracker.trajectory_modifiers.settle_in_polygon.SettleInPolygon

**short class_name:** SettleInPolygon

docs>>

**Inheritance:** > ParameterBaseClass> _BaseTrajectoryModifier> SettleInPolygon


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``polygon``: nested parameter dictionary

	points: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``probability_of_settlement`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``

	* ``settlement_duration`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``
		- min: ``0.0``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


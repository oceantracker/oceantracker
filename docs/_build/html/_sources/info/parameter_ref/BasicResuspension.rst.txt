##################
BasicResuspension
##################

**Doc:**     A very basic resupension, resuspend a distance of random walk, with variance equal to the constant vertical eddy viscosity     

**short class_name:** BasicResuspension

**full class_name :** oceantracker.resuspension.basic_resuspension.BasicResuspension


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseResuspension> Resuspension> BasicResuspension


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``critical_friction_velocity`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- min: ``0.0``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		- default: ``BasicResuspension``
		- data_type: ``<class 'str'>``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``



Expert Parameters:
*******************



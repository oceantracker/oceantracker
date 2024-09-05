###########
RandomWalk
###########

**Doc:**     implements random walk of particles by adding equivalent random velocity    

**short class_name:** RandomWalk

**full class_name :** oceantracker.dispersion.random_walk.RandomWalk

**Inheritance:** > ParameterBaseClass> BaseTrajectoryModifer> RandomWalk


Parameters:
************

	* ``A_H`` :   ``<class 'float'>``   *<optional>*
		Description: Horizontal turbulent eddy viscosity

		- default: ``0.1``
		- data_type: ``<class 'float'>``
		- units: ``m/s^2``
		- min: ``0.0``

	* ``A_V`` :   ``<class 'float'>``   *<optional>*
		Description: Constant vertical turbulent eddy viscosity

		- default: ``0.01``
		- data_type: ``<class 'float'>``
		- units: ``m/s^2``
		- min: ``0.0``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``is3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

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



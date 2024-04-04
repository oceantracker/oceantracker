###########
RandomWalk
###########

**Description:** 

**full class_name :** oceantracker.dispersion.random_walk.RandomWalk

**short class_name:** RandomWalk

    implements random walk of particles by adding equivalent random velocity    

**Inheritance:** > ParameterBaseClass> _BaseTrajectoryModifer> RandomWalk


Parameters:
************

	* ``A_H`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.1``
		- min: ``0.0``

	* ``A_V`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.01``
		- min: ``0.0``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``is3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


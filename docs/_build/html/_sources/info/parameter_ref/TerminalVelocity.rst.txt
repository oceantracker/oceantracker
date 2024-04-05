#################
TerminalVelocity
#################

**Doc:** 

**short class_name:** TerminalVelocity

**full class_name :** oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity

**Inheritance:** > ParameterBaseClass> VelocityModiferBase> TerminalVelocity


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``is3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- required_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``
		- expert: ``False``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``
		- required_type: ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``
		- expert: ``False``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``value`` :   ``<class 'float'>``   *<optional>*
		Description: Terminal velocity positive upwards, ie fall velocities ate negative

		- default: ``0.0``
		- required_type: ``<class 'float'>``
		- expert: ``False``

	* ``variance`` :   ``<class 'float'>``   *<optional>*
		Description: variance of normal distribution of terminal velocity, used to give each particles its own terminal velocity from random normal distribution

		- default: ``None``
		- required_type: ``<class 'float'>``
		- min: ``0.0``
		- expert: ``False``



Expert Parameters:
*******************



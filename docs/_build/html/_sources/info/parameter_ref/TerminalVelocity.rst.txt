#################
TerminalVelocity
#################

**Doc:** 

**short class_name:** TerminalVelocity

**full class_name :** oceantracker.velocity_modifiers.terminal_velocity.TerminalVelocity

**Inheritance:** > ParameterBaseClass> _VelocityModiferBase> TerminalVelocity


Parameters:
************

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

	* ``value`` :   ``<class 'float'>``   *<optional>*
		Description: Terminal velocity positive upwards, ie fall velocities ate negative

		- default: ``0.0``
		- data_type: ``<class 'float'>``

	* ``variance`` :   ``<class 'float'>``   *<optional>*
		Description: variance of normal distribution of terminal velocity, used to give each particles its own terminal velocity from random normal distribution

		- default: ``None``
		- data_type: ``<class 'float'>``
		- min: ``0.0``



Expert Parameters:
*******************



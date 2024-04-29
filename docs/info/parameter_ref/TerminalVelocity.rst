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
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``is3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``value`` :   ``<class 'float'>``   *<optional>*
		Description: Terminal velocity positive upwards, ie fall velocities ate negative

		- default: ``0.0``
		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``variance`` :   ``<class 'float'>``   *<optional>*
		Description: variance of normal distribution of terminal velocity, used to give each particles its own terminal velocity from random normal distribution

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``0.0``



Expert Parameters:
*******************



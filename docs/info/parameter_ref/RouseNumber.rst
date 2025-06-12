############
RouseNumber
############

**Doc:**     calculate seabed Rouse number P, ration of fall velocity to turbulent pumping velocity    from friction velocity. Default is for sea bed. Requires a "terminal_velocity" "velocity_modfier to be added"    Can  estimate sea surface Rouse number if requested and   wind_stress variable is present in hydro files.    

**short class_name:** RouseNumber

**full class_name :** oceantracker.particle_properties.rouse_number.RouseNumber


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseParticleProperty> CustomParticleProperty> RouseNumber


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``dtype`` :   ``<class 'str'>``   *<optional>*
		- default: ``float64``
		- data_type: ``<class 'str'>``
		- possible_values: ``['float64', 'float32', 'bool', 'int32', 'int16', 'int8', 'int64']``

	* ``extra_dimensions``:  *<optional>*
		Description: - list of the names of dimensions for vectors, or those with prop_dim3 set. Partile is added automatically

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``initial_value`` :   ``<class 'float'>``   *<optional>*
		Description: Value given to particle property on release

		- default: ``0.0``
		- data_type: ``<class 'float'>``

	* ``name`` :   ``<class 'str'>`` **<isrequired>**
		Description: Name used to refer to this particle property in code and output

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``prop_dim3`` :   ``<class 'int'>``   *<optional>*
		Description: size of a 3d dimension of particle property

		- default: ``1``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``sea_bed`` :   ``<class 'bool'>``   *<optional>*
		Description: calculate seabed Rouse number, otherwise nea surface

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- units: ``dimension ;less``
		- possible_values: ``[True, False]``

	* ``terminal_velocity_name`` :   ``<class 'str'>`` **<isrequired>**
		Description: internal name assigned to user added terminal_velocity "trajectory_modifier class"

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``units`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``update`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``vector_dim`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write particle property to tracks or event files file

		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



Expert Parameters:
*******************

	* ``release_group_parameters``:  *<optional>*
		Description: - In development: release group specific particle prop params

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'str'>``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``



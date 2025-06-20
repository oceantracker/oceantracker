##############
RadiusRelease
##############

**Doc:**     Release particles at random locations within a radius of given points    Points chosen are always inside the domain, also inside wet cells unless setting allow_release_in_dry_cells is True.    

**short class_name:** RadiusRelease

**full class_name :** oceantracker.release_groups.radius_release.RadiusRelease


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> _BaseReleaseGroup> RadiusRelease


Parameters:
************

	* ``allow_release_in_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide.

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``duration`` :   ``<class 'float'>``   *<optional>*
		Description: How long particles are released for after they start being released, ie releases stop this time after first release.,an alternative to using "end"

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``0.0``

	* ``end`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: date/time of lase release, ignored if duration given

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``max_age`` :   ``<class 'float'>``   *<optional>*
		Description: Particles older than this age in seconds are culled,ie. status=dead, and removed from computation, very useful in reducing run time

		- default: ``None``
		- data_type: ``<class 'float'>``
		- min: ``1.0``

	* ``max_cycles_to_find_release_points`` :   ``<class 'int'>``   *<optional>*
		Description: Maximum number of cycles to search for acceptable release points, ie. inside domain, polygon etc

		- default: ``100``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``


points: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``pulse_size`` :   ``<class 'int'>``   *<optional>*
		Description: Number of particles released in a single pulse, this number is released every release_interval.

		- default: ``1``
		- data_type: ``<class 'int'>``
		- min: ``1``

	* ``radius`` :   ``<class 'float'>`` **<isrequired>**
		Description: Particles are released from random locations in circle of same given radius around each point.

		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- units: ``meters, even if hydromodel grid systen is (lon,lat)``
		- min: ``1.0``

	* ``release_at_bottom`` :   ``<class 'bool'>``   *<optional>*
		Description: 3D release particles at bottom, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``release_at_surface`` :   ``<class 'bool'>``   *<optional>*
		Description: 3D release particles at free surface, ie tide height, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``release_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time interval between released pulses. To release at only one time use release_interval=0.

		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- units: ``sec``
		- min: ``0.0``

	* ``release_offset_from_surface_or_bottom`` :   ``<class 'float'>``   *<optional>*
		Description: 3D release particles at offset from free surface or bottom, if release_at_surface or  release_at_bottom = True

		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- units: ``m``
		- min: ``0.0``

	* ``start`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: start date/time of first release"

		- default: ``None``
		- possible_types: ``[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>]``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``user_release_groupID`` :   ``<class 'int'>``   *<optional>*
		Description: User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.

		- default: ``0``
		- data_type: ``<class 'int'>``

	* ``user_release_group_name`` :   ``<class 'str'>``   *<optional>*
		Description: User given name/label to attached to this release groups to make it easier to distinguish.

		- default: ``no_given``
		- data_type: ``<class 'str'>``

	* ``water_depth_max`` :   ``<class 'float'>``   *<optional>*
		Description: max water depth to release in, normally >0

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``m``

	* ``water_depth_min`` :   ``<class 'float'>``   *<optional>*
		Description: min water depth to release in, normally >0, useful for releases with a depth rage, eg larvae from inter-tidal shellfish

		- default: ``None``
		- data_type: ``<class 'float'>``
		- units: ``m``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: max/ highest z vale release for to randomly release in 3D, overrides any given release z value

		- default: ``None``
		- data_type: ``<class 'float'>``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: min/ deepest z value to release for to randomly release in 3D, overrides any given release z value

		- default: ``None``
		- data_type: ``<class 'float'>``



Expert Parameters:
*******************



##############################
PolygonReleaseWaterDepthRange
##############################

**Doc:** 

**short class_name:** PolygonReleaseWaterDepthRange

**full class_name :** oceantracker.release_groups.polygon_release_water_depth_range.PolygonReleaseWaterDepthRange

**Inheritance:** > ParameterBaseClass> _BaseReleaseGroup> PointRelease> PolygonRelease> PolygonReleaseWaterDepthRange


Parameters:
************

	* ``allow_release_in_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide.

		- default: ``False``
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``duration`` :   ``<class 'float'>``   *<optional>*
		Description: How long particles are released for after they start being released, ie releases stop this time after first release.,an alternative to using "end"

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- units: ``sec``
		- min: ``0.0``

	* ``end`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: date/time of lase release, ignored if duration given

		- default: ``None``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``max_age`` :   ``<class 'float'>``   *<optional>*
		Description: Particles older than this age in seconds are culled,ie. status=dead, and removed from computation, very useful in reducing run time

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``1.0``

	* ``max_cycles_to_find_release_points`` :   ``<class 'int'>``   *<optional>*
		Description: Maximum number of cycles to search for acceptable release points, ie. inside domain, polygon etc

		- default: ``1000``
		- default: ``1000``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``100``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``


points: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``pulse_size`` :   ``<class 'int'>``   *<optional>*
		Description: Number of particles released in a single pulse, this number is released every release_interval.

		- default: ``1``
		- default: ``1``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``1``

	* ``release_at_bottom`` :   ``<class 'bool'>``   *<optional>*
		Description: 3D release particles at bottom, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value

		- default: ``False``
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``

	* ``release_at_surface`` :   ``<class 'bool'>``   *<optional>*
		Description: 3D release particles at free surface, ie tide height, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value

		- default: ``False``
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``

	* ``release_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time interval between released pulses. To release at only one time use release_interval=0.

		- default: ``0.0``
		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- units: ``sec``
		- min: ``0.0``

	* ``release_offset_from_surface_or_bottom`` :   ``<class 'float'>``   *<optional>*
		Description: 3D release particles at offset from free surface or bottom, if release_at_surface or  release_at_bottom = True

		- default: ``0.0``
		- default: ``0.0``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``
		- units: ``m``
		- min: ``0.0``

	* ``start`` :   ``['str', 'float', 'datetime64', 'int', 'float64', 'float32']``   *<optional>*
		Description: start date/time of first release"

		- default: ``None``
		- units: ``ISO8601  date as string eg. "2017-01-01T00:30:00",np.datetime64, or float of seconds since 1/1/1970``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``user_polygonID`` :   ``<class 'int'>``   *<optional>*
		- default: ``0``
		- default: ``0``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``0``

	* ``user_release_groupID`` :   ``<class 'int'>``   *<optional>*
		Description: User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.

		- default: ``0``
		- default: ``0``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``user_release_group_name`` :   ``<class 'str'>``   *<optional>*
		Description: User given name/label to attached to this release groups to make it easier to distinguish.

		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``water_depth_max`` :   ``<class 'float'>``   *<optional>*
		- default: ``1e+37``
		- default: ``1e+37``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``water_depth_min`` :   ``<class 'float'>``   *<optional>*
		- default: ``-1e+37``
		- default: ``-1e+37``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: max/ highest z vale release for to randomly release in 3D, overrides any given release z value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: min/ deepest z value to release for to randomly release in 3D, overrides any given release z value

		- default: ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``z_range``:  *<optional>*
		Description: - use z_min and/or z_max

		- a list containing type:  ``[]``
		- default list : ``None``
		- data_type: ``<class 'float'>``
		- expert: ``False``
		- obsolete: ``True``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``2``



Expert Parameters:
*******************



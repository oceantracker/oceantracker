###############
PolygonRelease
###############

**Description:** Release particles at random locations within given polygon. Points chosen are always inside the domain, also inside wet cells unless  allow_release_in_dry_cells is True.

**class_name:** oceantracker.release_groups.polygon_release.PolygonRelease

**File:** oceantracker/release_groups/polygon_release.py

**Inheritance:** PointRelease> PolygonRelease


Parameters:
************

	* ``allow_release_in_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide.

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``max_age`` :   ``<class 'float'>``   *<optional>*
		Description: Particles older than this age in seconds are culled,ie. status=dead, and removed from computation, very useful in reducing run time

		- default: ``None``
		- min: ``1.0``

	* ``max_cycles_to_find_release_points`` :   ``<class 'int'>``   *<optional>*
		Description: Maximum number of cycles to search for acceptable release points, ie. inside domain, polygon etc

		- default: ``200``
		- min: ``100``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


points: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``pulse_size`` :   ``<class 'int'>``   *<optional>*
		Description: Number of particles released in a single pulse, this number is released every release_interval.

		- default: ``1``
		- min: ``1``

	* ``release_at_bottom`` :   ``<class 'bool'>``   *<optional>*
		Description: 3D release particles at bottom, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``release_at_surface`` :   ``<class 'bool'>``   *<optional>*
		Description: 3D release particles at free surface, ie tide height, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``release_duration`` :   ``<class 'float'>``   *<optional>*
		Description: Time in seconds particles are released for after they start being released, ie releases stop this time after first release.,an alternative to using "release_end_date"

		- default: ``None``
		- min: ``0.0``

	* ``release_end_date`` :   ``iso8601date``   *<optional>*
		Description: Date to stop releasing particles, ignored if release_duration give, must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``

	* ``release_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time interval between released pulses. To release at only one time use release_interval=0.

		- default: ``0.0``
		- min: ``0.0``
		- units: ``sec``

	* ``release_offset_from_surface_or_bottom`` :   ``[<class 'float'>, <class 'int'>]``   *<optional>*
		Description: 3D release particles at offset from free surface or bottom, if release_at_surface or  release_at_bottom = True

		- default: ``0.0``
		- min: ``0.0``
		- units: ``m``

	* ``release_start_date`` :   ``iso8601date``   *<optional>*
		Description: Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``user_polygonID`` :   ``<class 'int'>``   *<optional>*
		- default: ``0``
		- min: ``0``

	* ``user_release_groupID`` :   ``<class 'int'>``   *<optional>*
		Description: User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.

		- default: ``0``

	* ``user_release_group_name`` :   ``<class 'str'>``   *<optional>*
		Description: User given name/label to attached to this release groups to make it easier to distinguish.

		- default: ``None``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: max/ highest z vale release for to randomly release in 3D, overrides any given release z value

		- default: ``None``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: min/ deepest z value to release for to randomly release in 3D, overrides any given release z value

		- default: ``None``

	* ``z_range``:  *<optional>*
		- a list containing type:  ``[<class 'float'>, <class 'int'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- min_length: ``2``
		- obsolete: ``use z_min and/or z_max``


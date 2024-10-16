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

		- default: ``50``
		- min: ``50``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``points`` :   ``array`` **<isrequired>**
		Description: Points making up the polygon as, N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array

		- default: ``[]``
		- list_contains_type: ``<class 'float'>``

	* ``pulse_size`` :   ``<class 'int'>``   *<optional>*
		Description: Number of particles released in a single pulse, this number is released every release_interval.

		- default: ``1``
		- min: ``1``

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

	* ``z_range``:  *<optional>*
		Description: - z range = [zmin, zmax] to randomly release in 3D, overrides any given release z value

		- a list containing type:  ``[<class 'float'>, <class 'int'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- min_length: ``2``


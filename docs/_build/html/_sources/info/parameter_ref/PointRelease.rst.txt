#############
PointRelease
#############

**Description:** Release particles at 1 or more given locations. Pulse_size particles are released every release_interval. All these particles are tagged as a single release_group.

**Class:** oceantracker.particle_release_groups.point_release.PointRelease

**File:** oceantracker/particle_release_groups/point_release.py

**Inheritance:** PointRelease

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``allow_release_in_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: - Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide.

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``max_cycles_to_find_release_points`` :   ``<class 'int'>``   *<optional>*
		Description: - Maximum number of cycles to search for acceptable release points, ie. inside domain, polygon etc

		- default: ``50``
		- min: ``50``

	* ``maximum_age`` :   ``<class 'float'>``   *<optional>*
		Description: - Particles older than this age in seconds are killed off and removed from computation.

		- default: ``None``
		- min: ``1.0``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- default: ``None``

	* ``points`` :   ``vector`` **<isrequired>**
		Description: - A N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array

		- default: ``[]``

	* ``pulse_size`` :   ``<class 'int'>``   *<optional>*
		Description: - Number of particles released in a single pulse, this number is released every release_interval.

		- default: ``1``
		- min: ``1``

	* ``release_duration`` :   ``<class 'float'>``   *<optional>*
		Description: - Time in seconds particles are released for after they start being released, ie releases stop this time after first release.

		- default: ``None``
		- min: ``0.0``

	* ``release_end_date`` :   ``iso8601date``   *<optional>*
		Description: - Date to stop releasing partices, ignored if release_duration give, must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``

	* ``release_interval`` :   ``<class 'float'>``   *<optional>*
		Description: - Time interval between released pulses. To release at only one time use release_interval=0.

		- default: ``0.0``
		- min: ``0.0``

	* ``release_radius`` :   ``<class 'float'>``   *<optional>*
		Description: - Particles are released from random locations in circle of given radius around each point.

		- default: ``0.0``
		- min: ``0.0``

	* ``release_start_date`` :   ``iso8601date``   *<optional>*
		Description: - Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``user_particle_property_parameters``: nested parameter dictionary
	* ``user_release_groupID`` :   ``<class 'int'>``   *<optional>*
		Description: - User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.

		- default: ``0``

	* ``user_release_group_name`` :   ``<class 'str'>``   *<optional>*
		Description: - User given name/label to attached to this release groups to make it easier to distinguish.

		- default: ``None``

	* ``z_range``:  *<optional>*
		Description: - z range = [zmin, zmax] to randomly release in 3D, overrides any given release z value

		- a list containing type:  ``[<class 'float'>, <class 'int'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- min_length: ``2``


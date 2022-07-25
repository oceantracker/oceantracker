###############
PolygonRelease
###############

**Description:** Release particles at random locations within given polygon. Points chosen are always inside the domain, also inside wet cells unless  allow_release_in_dry_cells is True.

**Class:** oceantracker.particle_release_groups.polygon_release.PolygonRelease

**File:** oceantracker/particle_release_groups/polygon_release.py

**Inheritance:** PointRelease> PolygonRelease

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``allow_release_in_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: - Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``maximum_age`` :   ``<class 'float'>``   *<optional>*
		Description: - Particles older than this are killed off and removed from computation.

		- default: ``1e+32``
		- min: ``1.0``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- default: ``None``

	* ``points`` :   ``vector`` **<isrequired>**
		- default: ``[]``
		- list_contains_type: ``<class 'float'>``

	* ``pulse_size`` :   ``<class 'int'>``   *<optional>*
		Description: - Number of particles is a single pulse.

		- default: ``1``
		- min: ``1``

	* ``release_duration`` :   ``<class 'float'>``   *<optional>*
		Description: - Time particles are released for after they start being released, ie releases stop this time after first release.

		- default: ``1e+32``
		- min: ``0``

	* ``release_interval`` :   ``<class 'float'>``   *<optional>*
		Description: - Time interval between released pulses.

		- default: ``0.0``
		- min: ``0.0``

	* ``release_start_date`` :   ``iso8601date``   *<optional>*
		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``user_particle_property_parameters``: nested parameter dictionary
	* ``user_polygonID`` :   ``<class 'int'>``   *<optional>*
		- default: ``0``
		- min: ``0``

	* ``user_polygon_name`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``user_release_group_ID`` :   ``<class 'int'>``   *<optional>*
		Description: - User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.

		- default: ``0``

	* ``user_release_group_name`` :   ``<class 'str'>``   *<optional>*
		Description: - User given name/label to attached to this release groups to make it easier to distinguish.

		- default: ``None``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: - Max. z cord value to release with the polygon

		- default: ``0.0``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: - Min. z cord value to release with the polygon

		- default: ``0.0``


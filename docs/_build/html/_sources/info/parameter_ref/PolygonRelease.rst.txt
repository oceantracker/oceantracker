###############
PolygonRelease
###############

**Class:** oceantracker.particle_release_groups.polygon_release.PolygonRelease

**File:** oceantracker/particle_release_groups/polygon_release.py

**Inheritance:** PointRelease> PolygonRelease

**Default internal name:** ``"not given in defaults"``

**Description:** Release particles at random locations within given polygon. Points chosen are always inside the domain, also inside wet cells unless  allow_release_in_dry_cells is True.


Parameters:
************

	* ``allow_release_in_dry_cells``:  *<optional>*
		**Description:** - Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide

		- type: ``<class 'bool'>``
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``class_name``:  *<optional>*
		**Description:** - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``doc_str``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``Release particles at random locations within given polygon. Points chosen are always inside the domain, also inside wet cells unless  allow_release_in_dry_cells is True.``

	* ``maximum_age``:  *<optional>*
		**Description:** - Particles older than this are killed off and removed from computation.

		- type: ``<class 'float'>``
		- default: ``1e+32``
		- min: ``1.0``

	* ``name``:  *<optional>*
		**Description:** - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- type: ``<class 'str'>``
		- default: ``None``

	**<isrequired>**
		- type: ``vector``
		- default: ``[]``
		- list_contains_type: ``<class 'float'>``

	* ``pulse_size``:  *<optional>*
		**Description:** - Number of particles is a single pluse.

		- type: ``<class 'int'>``
		- default: ``1``
		- min: ``1``

	* ``release_duration``:  *<optional>*
		**Description:** - Time particles are released for after they start being released, ie releases stop this time after first release.

		- type: ``<class 'float'>``
		- default: ``1e+32``
		- min: ``0``

	* ``release_interval``:  *<optional>*
		**Description:** - Time interval between released pulses.

		- type: ``<class 'float'>``
		- default: ``0.0``
		- min: ``0.0``

	* ``release_start_date``:  *<optional>*
		- type: ``iso8601date``
		- default: ``None``

	* ``release_z``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``0.0``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


user_particle_property_parameters: still working on display  of nested  params dict <class 'dict'>

	* ``user_polygonID``:  *<optional>*
		- type: ``<class 'int'>``
		- default: ``0``
		- min: ``0``

	* ``user_polygon_name``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``user_release_group_ID``:  *<optional>*
		**Description:** - User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.

		- type: ``<class 'int'>``
		- default: ``0``

	* ``user_release_group_name``:  *<optional>*
		**Description:** - User given name/label to attached to this release groups to make it easier to distinguish.

		- type: ``<class 'str'>``
		- default: ``None``

	* ``z_max``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``0.0``

	* ``z_min``:  *<optional>*
		- type: ``<class 'float'>``
		- default: ``0.0``


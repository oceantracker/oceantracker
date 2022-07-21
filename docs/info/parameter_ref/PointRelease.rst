#############
PointRelease
#############

**Class:** oceantracker.particle_release_groups.point_release.PointRelease

**File:** oceantracker/particle_release_groups/point_release.py

**Inheritance:** PointRelease

**Default internal name:** ``"not given in defaults"``

**Description:** Release particles at 1 or more given locations. Pulse_size particles are released every release_interval. All these particles are tagged as a single release_group.


Parameters:
************

	* ``class_name``:  *<optional>*
		**Description:** - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``doc_str``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``Release particles at 1 or more given locations. Pulse_size particles are released every release_interval. All these particles are tagged as a single release_group.``

	* ``maximum_age``:  *<optional>*
		**Description:** - Particles older than this are killed off and removed from computation.

		- type: ``<class 'float'>``
		- default: ``1e+32``
		- min: ``1.0``

	* ``name``:  *<optional>*
		**Description:** - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field

		- type: ``<class 'str'>``
		- default: ``None``

	**<isrequired>**
		**Description:** - List of points where particles are released

		- type: ``vector``
		- default: ``[]``

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

	* ``release_radius``:  *<optional>*
		**Description:** - Particles are released from random locations in circle of given radius around each point.

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

	* ``user_release_group_ID``:  *<optional>*
		**Description:** - User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.

		- type: ``<class 'int'>``
		- default: ``0``

	* ``user_release_group_name``:  *<optional>*
		**Description:** - User given name/label to attached to this release groups to make it easier to distinguish.

		- type: ``<class 'str'>``
		- default: ``None``


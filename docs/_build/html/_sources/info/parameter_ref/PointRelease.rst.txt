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

	* ``class_name``:  *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``description``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``maximum_age``:  *<optional>*
		Description: - Particles older than this are killed off and removed from computation.

		- type: ``<class 'float'>``
		- default: ``1e+32``
		- min: ``1.0``

	* ``name``:  *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- type: ``<class 'str'>``
		- default: ``None``

	* ``points``:**<isrequired>**
		Description: - A N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array

		- type: ``vector``
		- default: ``[]``

	* ``pulse_size``:  *<optional>*
		Description: - Number of particles is a single pulse.

		- type: ``<class 'int'>``
		- default: ``1``
		- min: ``1``

	* ``release_duration``:  *<optional>*
		Description: - Time particles are released for after they start being released, ie releases stop this time after first release.

		- type: ``<class 'float'>``
		- default: ``1e+32``
		- min: ``0``

	* ``release_interval``:  *<optional>*
		Description: - Time interval between released pulses.

		- type: ``<class 'float'>``
		- default: ``0.0``
		- min: ``0.0``

	* ``release_radius``:  *<optional>*
		Description: - Particles are released from random locations in circle of given radius around each point.

		- type: ``<class 'float'>``
		- default: ``0.0``
		- min: ``0.0``

	* ``release_start_date``:  *<optional>*
		- type: ``iso8601date``
		- default: ``None``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``user_particle_property_parameters``: nested parameter dictionary
	* ``user_release_group_ID``:  *<optional>*
		Description: - User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.

		- type: ``<class 'int'>``
		- default: ``0``

	* ``user_release_group_name``:  *<optional>*
		Description: - User given name/label to attached to this release groups to make it easier to distinguish.

		- type: ``<class 'str'>``
		- default: ``None``


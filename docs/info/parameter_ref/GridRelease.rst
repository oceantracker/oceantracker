############
GridRelease
############

**Doc:**     Release pules of particles on a regular grid.    

**short class_name:** GridRelease

**full class_name :** oceantracker.release_groups.grid_release.GridRelease

**Inheritance:** > ParameterBaseClass> _BaseReleaseGroup> GridRelease


Parameters:
************

	* ``allow_release_in_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: Allow releases in cells which are currently dry, ie. either permanently dry or temporarily dry due to the tide.

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``
		- expert: ``False``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``duration`` :   ``<class 'float'>``   *<optional>*
		Description: How long particles are released for after they start being released, ie releases stop this time after first release.,an alternative to using "end"

		- default: ``None``
		- required_type: ``<class 'float'>``
		- min: ``0.0``
		- units: ``sec``
		- expert: ``False``

	* ``end`` :   ``iso8601date``   *<optional>*
		Description: Date to stop releasing particles, ignored if release_duration give Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``
		- required_type: ``iso8601date``
		- expert: ``False``


grid_center: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``grid_size``:  *<optional>*
		Description: - number of rows and columns in grid

		- a list containing type:  ``[<class 'int'>]``
		- default list : ``[100, 99]``
		- can_be_empty_list: ``True``
		- fixed_len: ``2``
		- min: ``1``
		- max: ``1000000``
		- expert: ``False``


grid_span: still working on display  of default params of  type <class 'oceantracker.util.parameter_checking.ParameterCoordsChecker'>

	* ``max_age`` :   ``<class 'float'>``   *<optional>*
		Description: Particles older than this age in seconds are culled,ie. status=dead, and removed from computation, very useful in reducing run time

		- default: ``None``
		- required_type: ``<class 'float'>``
		- min: ``1.0``
		- expert: ``False``

	* ``max_cycles_to_find_release_points`` :   ``<class 'int'>``   *<optional>*
		Description: Maximum number of cycles to search for acceptable release points, ie. inside domain, polygon etc

		- default: ``1000``
		- required_type: ``<class 'int'>``
		- min: ``100``
		- expert: ``False``

	* ``pulse_size`` :   ``<class 'int'>``   *<optional>*
		Description: Number of particles released in a single pulse, this number is released every release_interval.

		- default: ``1``
		- required_type: ``<class 'int'>``
		- min: ``1``
		- expert: ``False``

	* ``release_at_bottom`` :   ``<class 'bool'>``   *<optional>*
		Description: 3D release particles at bottom, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``
		- expert: ``False``

	* ``release_at_surface`` :   ``<class 'bool'>``   *<optional>*
		Description: 3D release particles at free surface, ie tide height, with  offset given by release_offset_from_surface_or_bottom param, overrides any given release z value

		- default: ``False``
		- required_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``
		- expert: ``False``

	* ``release_interval`` :   ``<class 'float'>``   *<optional>*
		Description: Time interval between released pulses. To release at only one time use release_interval=0.

		- default: ``0.0``
		- required_type: ``<class 'float'>``
		- min: ``0.0``
		- units: ``sec``
		- expert: ``False``

	* ``release_offset_from_surface_or_bottom`` :   ``[<class 'float'>, <class 'int'>]``   *<optional>*
		Description: 3D release particles at offset from free surface or bottom, if release_at_surface or  release_at_bottom = True

		- default: ``0.0``
		- required_type: ``[<class 'float'>, <class 'int'>]``
		- min: ``0.0``
		- units: ``m``
		- expert: ``False``

	* ``start`` :   ``iso8601date``   *<optional>*
		Description: start date of release, Must be an ISO date as string eg. "2017-01-01T00:30:00"

		- default: ``None``
		- required_type: ``iso8601date``
		- expert: ``False``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``
		- required_type: ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``
		- expert: ``False``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``user_release_groupID`` :   ``<class 'int'>``   *<optional>*
		Description: User given ID number for this group, held by each particle. This may differ from internally uses release_group_ID.

		- default: ``0``
		- required_type: ``<class 'int'>``
		- expert: ``False``

	* ``user_release_group_name`` :   ``<class 'str'>``   *<optional>*
		Description: User given name/label to attached to this release groups to make it easier to distinguish.

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``z_max`` :   ``<class 'float'>``   *<optional>*
		Description: max/ highest z vale release for to randomly release in 3D, overrides any given release z value

		- default: ``None``
		- required_type: ``<class 'float'>``
		- expert: ``False``

	* ``z_min`` :   ``<class 'float'>``   *<optional>*
		Description: min/ deepest z value to release for to randomly release in 3D, overrides any given release z value

		- default: ``None``
		- required_type: ``<class 'float'>``
		- expert: ``False``

	* ``z_range``:  *<optional>*
		- a list containing type:  ``[<class 'float'>, <class 'int'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- min_length: ``2``
		- obsolete: ``use z_min and/or z_max``
		- expert: ``False``



Expert Parameters:
*******************



##################
ResidentInPolygon
##################

**Description:** 

**Class:** oceantracker.particle_statistics.resident_in_polygon.ResidentInPolygon

**File:** oceantracker/particle_statistics/resident_in_polygon.py

**Inheritance:** _BaseParticleLocationStats> ResidentInPolygon

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``count_end_date`` :   ``iso8601date``   *<optional>*
		Description: - Stop particle counting from this date

		- default: ``None``

	* ``count_start_date`` :   ``iso8601date``   *<optional>*
		Description: - Start particle counting from this date

		- default: ``None``

	* ``count_status_in_range``:  *<optional>*
		Description: - Count only those particles with status which fall in the given range

		- a list containing type:  ``[<class 'str'>]``
		- default list : ``['frozen', 'moving']``
		- can_be_empty_list: ``True``
		- min_length: ``2``
		- max_length: ``2``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: - The internal name, which is used to reference the instance of this class within the code, eg. the name "water_velocity" would refers to a particle property or field used within the code

		- default: ``None``

	* ``name_of_polygon_release_group`` :   ``<class 'str'>`` **<isrequired>**
		Description: - "name" parameter of polygon release group to count paticles for residence time , (release group "name"  must be set by user). Particles inside this release groups polygon are conted to be used to calculate its residence time

		- default: ``None``

	* ``particle_property_list``:  *<optional>*
		- a list containing type:  ``[<class 'str'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- make_list_unique: ``True``

	* ``requires_3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``residence``

	* ``update_interval`` :   ``<class 'float'>``   *<optional>*
		Description: - Time in seconds between calculating statistics

		- default: ``3600.0``
		- units: ``sec``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``z_range``:  *<optional>*
		Description: - z range = [zmin, zmax] count particles in this z range in 3D

		- a list containing type:  ``[<class 'float'>, <class 'int'>]``
		- default list : ``[]``
		- can_be_empty_list: ``True``
		- min_length: ``2``


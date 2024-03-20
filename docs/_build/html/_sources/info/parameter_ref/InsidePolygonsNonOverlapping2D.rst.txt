###############################
InsidePolygonsNonOverlapping2D
###############################

**Description:** Index of polygon a particle is inside

**class_name:** oceantracker.particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D

**File:** oceantracker/particle_properties/inside_polygons.py

**Inheritance:** _BaseParticleProperty> ParticleProperty> InsidePolygonsNonOverlapping2D


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``dtype`` :   ``<class 'type'>``   *<optional>*
		- default: ``<class 'numpy.int32'>``

	* ``fill_value`` :   ``[<class 'int'>, <class 'float'>]``   *<optional>*
		- default: ``None``

	* ``initial_value`` :   ``<class 'int'>``   *<optional>*
		- default: ``-1``

	* ``polygon_list``:  *<optional>*

polygon_list: still working on display  of lists of dict, eg nested polygon list 

	* ``prop_dim3`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``release_group_parameters`` :   ``<class 'list'>``   *<optional>*
		Description: In development: release group specific particle prop params

		- default: ``[]``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``type`` :   ``<class 'str'>``   *<optional>*
		Description: type of particle property, used to manage how to update particle property

		- default: ``user``
		- possible_values: ``['manual_update', 'from_fields', 'user']``

	* ``update`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``user_instance_info`` :   ``[<class 'str'>, <class 'int'>, <class 'float'>, <class 'tuple'>, <class 'list'>]``   *<optional>*
		Description: a user setable ID which can be added information about the instance which remains in its params dict for later use, can be str, int,float, list or tuple

		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``vector_dim`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		Description: Write particle property to tracks or event files file

		- default: ``True``
		- possible_values: ``[True, False]``


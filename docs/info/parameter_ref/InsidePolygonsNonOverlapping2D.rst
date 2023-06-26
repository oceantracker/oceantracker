###############################
InsidePolygonsNonOverlapping2D
###############################

**Description:** Index of polygon a particle is inside

**class_name:** oceantracker.particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D

**File:** oceantracker/particle_properties/inside_polygons.py

**Inheritance:** _BasePropertyInfo> ParticleProperty> InsidePolygonsNonOverlapping2D


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

	* ``requires_3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``type`` :   ``<class 'str'>``   *<optional>*
		Description: particle property

		- default: ``user``
		- possible_values: ``['manual_update', 'from_fields', 'user']``

	* ``update`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``vector_dim`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


###############################
InsidePolygonsNonOverlapping2D
###############################

**Description:** Index of polygon a particle is inside

**Class:** oceantracker.particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D

**File:** oceantracker/particle_properties/inside_polygons.py

**Inheritance:** _BasePropertyInfo> ParticleProperty> InsidePolygonsNonOverlapping2D

**Default internal name:** ``"inside_polygons_non_overlapping"``


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``description`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``dtype`` :   ``<class 'type'>``   *<optional>*
		- default: ``<class 'numpy.int32'>``

	* ``initial_value`` :   ``<class 'int'>``   *<optional>*
		- default: ``-1``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		- default: ``inside_polygons_non_overlapping``

	* ``polygon_list``:  *<optional>*

polygon_list: still working on display  of lists of dict, eg nested polygon list 

	* ``prop_dim3`` :   ``<class 'int'>``   *<optional>*
		- default: ``1``
		- min: ``1``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``type`` :   ``<class 'str'>``   *<optional>*
		Description: - particle property

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


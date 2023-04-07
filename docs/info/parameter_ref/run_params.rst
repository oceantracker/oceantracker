###########
run_params
###########



Parameters:
************

	* ``block_dry_cells`` :   ``<class 'bool'>``   *<optional>*
		Description: - Block particles moving from wet to dry cells, ie. treat dry cells as if they are part of the lateral boundary

		- default: ``True``
		- possible_values: ``[True, False]``

	* ``case_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``duration`` :   ``<class 'float'>``   *<optional>*
		- default: ``1e+300``

	* ``open_boundary_type`` :   ``<class 'int'>``   *<optional>*
		- default: ``0``
		- min: ``0``
		- max: ``1``

	* ``particle_buffer_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``None``
		- min: ``1``

	* ``retain_culled_part_locations`` :   ``<class 'bool'>``   *<optional>*
		Description: - When particle marked dead/culled keep its position value, ie dont set position to nan so it does not appear in plots etc after death

		- default: ``False``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``No user note``

	* ``write_tracks`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``z0`` :   ``<class 'float'>``   *<optional>*
		- default: ``0.005``
		- min: ``0.0001``


#################
VerticalGradient
#################

**Description:** Calculated vertical gradient of "name_of_field" param, as  "name_of_field_vertical_grad"

**Class:** oceantracker.fields.field_vertical_gradient.VerticalGradient

**File:** oceantracker/fields/field_vertical_gradient.py

**Inheritance:** _BaseField> UserFieldBase> VerticalGradient

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``is3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``is_time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``name`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``

	* ``name_of_field`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``

	* ``num_components`` :   ``<class 'int'>``   *<optional>*
		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write_interp_particle_prop_to_tracks_file`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


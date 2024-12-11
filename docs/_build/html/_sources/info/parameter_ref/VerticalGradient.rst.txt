#################
VerticalGradient
#################

**Doc:** Add a vertical gradient field of the  "get_grad_of_field_named" param,    as a custom field named "get_grad_of_field_named_vertical_grad"'    

**short class_name:** VerticalGradient

**full class_name :** oceantracker.fields.field_vertical_gradient.VerticalGradient

**Inheritance:** > ParameterBaseClass> _BaseField> CustomFieldBase> VerticalGradient


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``create_particle_property_with_same_name`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``get_grad_of_field_named`` :   ``<class 'str'>`` **<isrequired>**
		Description: Name of field to calculate the vertical gradient of

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``is3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``is_vector`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``name`` :   ``<class 'str'>`` **<isrequired>**
		Description: Name to refer to this field internally within code, must be given

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``requires3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``write_interp_particle_prop_to_tracks_file`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



Expert Parameters:
*******************



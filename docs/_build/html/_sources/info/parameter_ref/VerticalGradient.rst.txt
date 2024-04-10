#################
VerticalGradient
#################

**Doc:** Add a vertical gradient field of the  "name_of_field" param,    as a custom field named "name_of_field_vertical_grad"'    

**short class_name:** VerticalGradient

**full class_name :** oceantracker.fields.field_vertical_gradient.VerticalGradient

**Inheritance:** > ParameterBaseClass> ReaderField> CustomFieldBase> VerticalGradient


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``create_particle_property_with_same_name`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``is3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``is_vector`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- required_type: ``<class 'bool'>``
		- expert: ``False``

	* ``name_of_field`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``
		- required_type: ``<class 'str'>``
		- expert: ``False``

	* ``time_varying`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- required_type: ``<class 'bool'>``
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

	* ``write_interp_particle_prop_to_tracks_file`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- required_type: ``<class 'bool'>``
		- expert: ``False``



Expert Parameters:
*******************



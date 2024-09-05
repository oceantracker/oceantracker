############
ReaderField
############

**Doc:** Feild to hold ring buffer of a variable read from hindcast files

**short class_name:** ReaderField

**full class_name :** oceantracker.fields.reader_field.ReaderField

**Inheritance:** > ParameterBaseClass> _BaseField> ReaderField


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

	* ``is3D`` :   ``<class 'bool'>`` **<isrequired>**
		Description: is field 3D

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``is_vector`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``

	* ``name`` :   ``<class 'str'>`` **<isrequired>**
		Description: Name used internally to refer to this field within the code

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``time_varying`` :   ``<class 'bool'>`` **<isrequired>**
		Description: Does field vary with time

		- default: ``False``
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

	* ``development`` :   ``<class 'bool'>``   *<optional>*
		Description: Class is under development and testing

		- default: ``False``
		- data_type: ``<class 'bool'>``
		- possible_values: ``[True, False]``



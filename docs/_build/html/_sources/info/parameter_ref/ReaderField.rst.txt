############
ReaderField
############

**Description:** 

**Class:** oceantracker.fields.reader_field.ReaderField

**File:** oceantracker/fields/reader_field.py

**Inheritance:** _BaseField> ReaderField

**Default internal name:** ``"not given in defaults"``


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``create_particle_property_with_same_name`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``dtype`` :   ``<class 'numpy.number'>``   *<optional>*
		- default: ``<class 'numpy.float64'>``

	* ``is3D`` :   ``<class 'bool'>`` **<isrequired>**
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``is_time_varying`` :   ``<class 'bool'>`` **<isrequired>**
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``name`` :   ``<class 'str'>`` **<isrequired>**
		- default: ``None``

	* ``num_components`` :   ``<class 'int'>`` **<isrequired>**
		- default: ``None``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``


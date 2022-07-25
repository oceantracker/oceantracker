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

	* ``class_name``:  *<optional>*
		Description: - Class name as string A.B.C, used to import this class from python path

		- type: ``<class 'str'>``
		- default: ``None``

	* ``create_particle_property_with_same_name``:  *<optional>*
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``description``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``

	* ``dtype``:  *<optional>*
		- type: ``<class 'numpy.dtype'>``
		- default: ``<class 'numpy.float64'>``

	* ``is3D``:**<isrequired>**
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``is_time_varying``:**<isrequired>**
		- type: ``<class 'bool'>``
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``name``:**<isrequired>**
		- type: ``<class 'str'>``
		- default: ``None``

	* ``num_components``:**<isrequired>**
		- type: ``<class 'int'>``
		- default: ``None``

	* ``user_note``:  *<optional>*
		- type: ``<class 'str'>``
		- default: ``None``


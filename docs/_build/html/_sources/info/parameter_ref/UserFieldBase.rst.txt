##############
UserFieldBase
##############

**Description:** 

**Class:** oceantracker.fields._base_field.UserFieldBase

**File:** oceantracker/fields/_base_field.py

**Inheritance:** _BaseField> UserFieldBase


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``

	* ``is3D`` :   ``<class 'bool'>`` **<isrequired>**
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``is_time_varying`` :   ``<class 'bool'>`` **<isrequired>**
		- default: ``True``
		- possible_values: ``[True, False]``

	* ``num_components`` :   ``<class 'int'>`` **<isrequired>**
		- default: ``None``

	* ``requires_3D`` :   ``<class 'bool'>``   *<optional>*
		- default: ``False``
		- possible_values: ``[True, False]``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``

	* ``write_interp_particle_prop_to_tracks_file`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- possible_values: ``[True, False]``


################
DevNestedFields
################

**Doc:**  Core class. Builds a list of field group managers for outer and nested grids and manage    interactions with list of field group managers. Eg update, interpolate etc     First in list grid is the outer grid.     Consistency between available hindcast variables means this code is fragile and error messages opaque.     

**short class_name:** DevNestedFields

**full class_name :** oceantracker.field_group_manager.dev_nested_grids_field_group_manager.DevNestedFields


.. warning::

	Class is under development may not yet work in all cases, if errors contact developer



**Inheritance:** > ParameterBaseClass> DevNestedFields


Parameters:
************

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``name`` :   ``<class 'str'>``   *<optional>*
		Description: Name used to refer to class in code and output, = None for core claseses

		- default: ``None``
		- data_type: ``<class 'str'>``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``



Expert Parameters:
*******************



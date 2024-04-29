#######################
LogPolygonEntryAndExit
#######################

**Doc:** 

**short class_name:** LogPolygonEntryAndExit

**full class_name :** oceantracker.event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit

**Inheritance:** > ParameterBaseClass> _BaseEventLogger> LogPolygonEntryAndExit


Parameters:
************

	* ``chunk_size`` :   ``<class 'int'>``   *<optional>*
		- default: ``500000``
		- default: ``500000``
		- data_type: ``<class 'int'>``
		- expert: ``False``
		- obsolete: ``False``
		- min: ``1``

	* ``class_name`` :   ``<class 'str'>``   *<optional>*
		Description: Class name as string A.B.C, used to import this class from python path

		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``particle_prop_to_write_list``:  *<optional>*
		- a list containing type:  ``[]``
		- default list : ``['ID', 'x', 'IDpulse', 'IDrelease_group', 'user_release_groupID', 'status', 'age']``
		- default: ``['ID', 'x', 'IDpulse', 'IDrelease_group', 'user_release_groupID', 'status', 'age']``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``polygon_list``:**<isrequired>**
		- a list containing type:  ``[]``
		- default list : ``{'user_polygonID': ParamValueChecker(default=0, data_type=<class 'int'>, expert=False, obsolete=False, is_required=False, doc_str=None, units=None, min=0, max=None, possible_values=None), 'name': ParamValueChecker(default=None, data_type=<class 'str'>, expert=False, obsolete=False, is_required=False, doc_str=None, units=None, min=None, max=None, possible_values=None), 'points': ParameterCoordsChecker(default=None, possible_types=[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>], expert=False, obsolete=False, is_required=True, doc_str='Points making up the polygon as, N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array', units='metres, or (lon, lat) as  decimal degrees if hindcast in (lon, lat) ', one_or_more_points=False, single_cord=False, is3D=False, min=None, max=None)}``
		- default: ``{'user_polygonID': ParamValueChecker(default=0, data_type=<class 'int'>, expert=False, obsolete=False, is_required=False, doc_str=None, units=None, min=0, max=None, possible_values=None), 'name': ParamValueChecker(default=None, data_type=<class 'str'>, expert=False, obsolete=False, is_required=False, doc_str=None, units=None, min=None, max=None, possible_values=None), 'points': ParameterCoordsChecker(default=None, possible_types=[<class 'str'>, <class 'float'>, <class 'numpy.datetime64'>, <class 'int'>, <class 'numpy.float64'>, <class 'numpy.float32'>], expert=False, obsolete=False, is_required=True, doc_str='Points making up the polygon as, N by 2 or 3 list of locations where particles are released. eg for 2D ``[[25,10],[23,2],....]``, must be convertible into N by 2 or 3 numpy array', units='metres, or (lon, lat) as  decimal degrees if hindcast in (lon, lat) ', one_or_more_points=False, single_cord=False, is3D=False, min=None, max=None)}``
		- data_type: ``<class 'dict'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_types: ``[]``
		- make_list_unique: ``False``
		- min_len: ``0``

	* ``role_output_file_tag`` :   ``<class 'str'>``   *<optional>*
		- default: ``inside_polygon_events``
		- default: ``inside_polygon_events``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``user_note`` :   ``<class 'str'>``   *<optional>*
		- default: ``None``
		- data_type: ``<class 'str'>``
		- expert: ``False``
		- obsolete: ``False``

	* ``write`` :   ``<class 'bool'>``   *<optional>*
		- default: ``True``
		- default: ``True``
		- data_type: ``<class 'bool'>``
		- expert: ``False``
		- obsolete: ``False``
		- possible_values: ``[True, False]``



Expert Parameters:
*******************



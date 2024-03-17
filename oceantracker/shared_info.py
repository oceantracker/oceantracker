# shared info
from oceantracker import  common_info_default_param_dict_templates as common_info
from oceantracker.util.class_importing_util import ClassImporter




from oceantracker.particle_properties import particle_operations as particle_operations


# set up class instances references from shared info
class __DummyObject(object):  pass
roles =  __DummyObject()
core_roles =  __DummyObject()
# make an empty attribute  structure to hold classes
for role in common_info.class_dicts_list :
    if not hasattr(roles,role):
        setattr(roles, role,  __DummyObject())

for role in common_info.core_class_list:
    if not hasattr(core_roles,role):
        setattr(core_roles, role,  __DummyObject())
pass


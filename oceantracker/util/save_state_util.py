from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.util import time_util, json_util
from os import path
def save_part_prop_state(file_name, si, n_time_step, time_sec ):
    # save particle properties
    nc = NetCDFhandler(file_name, mode='w')

    nc.create_attribute('time', time_sec)
    nc.create_attribute('date', time_util.seconds_to_isostr(time_sec))
    nc.create_attribute('n_time_step', n_time_step)

    nc.create_dimension(si.dim_names.particle, si.run_info.particles_in_buffer)
    for name, prop in si.class_roles.particle_properties.items():
        if not hasattr(prop,'data'): continue
        dims = [si.dim_names.particle]
        if prop.params['vector_dim'] == 2: dims += [si.dim_names.vector2D]
        if prop.params['vector_dim'] == 3: dims += [si.dim_names.vector3D]
        if prop.params['prop_dim3'] > 1: dims += ['dim3_' + name]


        #if len(dims) == prop.data.ndim:
            # in dev mode only write those that have al dimensions
            # add  dim 3 with a name
        nc.write_variable(name, prop.data[:si.run_info.particles_in_buffer, ...], dims)

    nc.close()

def get_class_info(si ):
        # record current state of all  class info
        d= dict(core_class_roles={},class_roles={},)
        for role, i in si.core_class_roles.items():
            if role is not None and hasattr(i, 'info'):
                d['core_class_roles'][role] = i.info

        for role, item in si.class_roles.items():
            if role not in d['class_roles']:  d['class_roles'][role] = dict()
            for name, i in item.items():
                d['class_roles'][role][name] = i.info
        return d




def save_settings_class_params(file_name, si):
    # recorded current state of all  class info
    d = dict(settings=si.settings.asdict(),
             run_info=si.run_info.asdict(),
             core_class_roles=dict(),
             class_roles=dict(),
             )
    for role, i in si.core_class_roles.items():
         if i is not None:
            d['core_class_roles'][role] = i.params

    for role, item in si.class_roles.items():
        if role not in d['class_roles']:  d['class_roles'][role] = dict()
        for name, i in item.items():
            d['class_roles'][role][name] = i.params

    # write info to json

    json_util.write_JSON(file_name, d)


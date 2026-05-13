import numpy as np
from numba.np.arrayobj import np_arange

from oceantracker.trajectory_modifiers._base_trajectory_modifers import _BaseTrajectoryModifier
from oceantracker.util.parameter_checking import ParamValueChecker as PVC
from oceantracker.shared_info import  shared_info as si
from oceantracker.util.ncdf_util import NetCDFhandler
from os import path
class KillAndLogStrandings(_BaseTrajectoryModifier):
    '''
    Kills particles when they first enter water ls than min. water depth param, and records this location
    also kills and record location of particles which exceed max age anf logs the location
    '''
    def __init__(self):
        # set up info/attributes
        super().__init__()  # required in children to get parent defaults
        self.add_default_params(
            max_age =  PVC(si.info.large_float, float, min=1., units='sec',
                      doc_str='Particles older than this age in seconds are culled,ie. status=dead, and removed from computation, very useful in reducing run time'),
            min_water_depth=PVC(2., float, min=0.0, units='m',
                            doc_str='Min. water depth used to decide if partile strands, not including tide'),
            output_file_base=PVC('stranding_log', str, doc_str='start of output file names'),
            )

    def initial_setup(self):
        self.open_file()
        pass

    def open_file(self):
        info = self.info
        params = self.params
        info['output_file'] = f'{params["output_file_base"]}_{info["instanceID"]:03}_{params["name"]}.nc'
        self.nc = NetCDFhandler(path.join(si.run_info.run_output_dir,info['output_file']),mode='w')
        nc = self.nc
        nc.create_dimension(si.dim_names.particle, None)
        nc.create_dimension(si.dim_names.vector2D, 2)
        part_chunk = 10**6
        nc.create_variable('x', [si.dim_names.particle,si.dim_names.vector2D],np.float64,
                           description='Location when first stranded in min. water depth', fill_value=np.nan, units='meters or degrees',
                        attributes=None, chunksizes=[part_chunk,2])
        nc.create_variable('eventID', [si.dim_names.particle, ], np.int8,
                           description='Type of venr, 1= stranded, -1 = died old age, 0 = nether stranded or old',
                           fill_value=0,
                           units='meters or degrees',
                           attributes=None, chunksizes=[part_chunk, ])
        nc.create_variable('status', [si.dim_names.particle, ], np.int8,
                           description='Particle status when removed',
                           attributes=dict(possible_values = "".join([f'{key}={val}, ' for key, val in si.particle_status_flags.items()])),
                           fill_value=si.particle_status_flags.notReleased,
                           chunksizes=[part_chunk, ])
        nc.create_variable('IDrelease_group', [si.dim_names.particle, ], np.int32,
                           description='Particles release group origin',
                           fill_value=-1,
                           units='meters or degrees',
                           attributes=None, chunksizes=[part_chunk, ])
        nc.create_variable('particleID', [si.dim_names.particle, ], np.int32,
                           description='Particle ID number',
                           fill_value=-1,
                           units='meters or degrees',
                           attributes=None, chunksizes=[si.settings.particle_buffer_initial_size, ])
        nc.create_variable('age', [si.dim_names.particle, ], np.float64,
                           description='Age wel killed', fill_value=np.nan,
                           units='seconds since 1970',
                           attributes=None, chunksizes=[si.settings.particle_buffer_initial_size, ])

        self.n_written=0
        pass

    def update(self,n_time_step, time_sec, active):
        pass
        part_prop = si.class_roles.particle_properties

        stranded = part_prop['water_depth'].find_subset_where(active, 'lteq', self.params['min_water_depth'],
                                                           out=self.get_partID_buffer('B1'))
        self.write_event(1, stranded)

        old = part_prop['age'].find_subset_where(active,'gt', self.params['max_age'],
                                                                   out=self.get_partID_buffer('B2'))
        self.write_event(-1, old)

        part_prop['status'].set_values(si.particle_status_flags.dead, stranded)
        part_prop['status'].set_values(si.particle_status_flags.dead, old)


    def write_event(self, eventID, sel):
        part_prop = si.class_roles.particle_properties
        nc = self.nc
        file_index= self.n_written + np.arange(sel.size)
        nc.file_handle['x'][file_index, ...] = part_prop['x'].data[sel, :2]
        nc.file_handle['eventID'][file_index] = eventID * np.ones((sel.size,), dtype=np.int8)
        nc.file_handle['IDrelease_group'][file_index] = part_prop['IDrelease_group'].data[sel]
        nc.file_handle['status'][file_index] = part_prop['status'].data[sel]
        nc.file_handle['age'][file_index] = part_prop['age'].data[sel]
        nc.file_handle['particleID'][file_index] = sel
        self.n_written += sel.size

    def close(self):
        self.nc.close()
from oceantracker.particle_statistics._base_location_stats import _BaseParticleLocationStats
from oceantracker.util.parameter_checking import  ParamValueChecker as PVC, ParameterCoordsChecker as PCC, merge_params_with_defaults
from copy import  deepcopy
from oceantracker.particle_statistics.util import stats_util
from oceantracker.util.numba_util import njitOT, njitOTparallel, prange

from oceantracker.shared_info import shared_info as si

import numpy as np
from numba import njit
#todo much clearner to  have user define polygon list for residence time per polygon like stats polygon!

class ResidentInPolygon(_BaseParticleLocationStats):
    '''
    Caculate residence times within a single given polygon for each release group'
    based on

    Lucas, L. V., & Deleersnijder, E. (2020). Timescale Methods for Simplifying, Understanding and Modeling Biophysical and Water Quality Processes in Coastal Aquatic Ecosystems: A Review. Water 2020, Vol. 12, Page 2717, 12(10), 2717. https://doi.org/10.3390/W12102717
    '''
    def __init__(self):
        # set up info/attributes
        super().__init__()

        self.add_default_params(points = PCC(None,doc_str='Points for 2D polygon to calc residence times, as N by 2 list or numpy array'),
                                update_interval=PVC(None, float,
                                                    doc_str='Nannt be set by user, as must equal time step'),

                                )

        # todo are prop values useful, add?
        self.remove_default_params(['particle_property_list'])
        self.development=True

    def add_required_classes_and_settings(self):
        # add polygon entry exit times class to use in residency calcs
        info = self.info
        params = self.params
        info['inside_polygon_prop'] = f'{params["name"]}_inside_polygon'
        si.add_class('particle_properties',
                     class_name='InsidePolygonsNonOverlapping2D',
                     name= info['inside_polygon_prop'],
                     write=False,
                     polygon_list=[dict(points=params['points'])])

        info['was_inside_polygon_prop'] = f'{params["name"]}_was_inside_polygon'
        si.add_class('particle_properties',
                 class_name='ManuallyUpdatedParticleProperty',
                 dtype = 'int32',
                initial_value=-1, # mark as inside no polygon
                 name=info['was_inside_polygon_prop'],
                 write=False)
        info['first_entry_time_prop'] = f'{params["name"]}_first_entry_time'
        si.add_class('particle_properties',
                 class_name='ManuallyUpdatedParticleProperty',
                 dtype='float64',
                initial_value = np.nan,
                 name=info['first_entry_time_prop'],
                 write=False)
        info['entry_count_prop'] = f'{params["name"]}_entry_count'
        si.add_class('particle_properties',
                     class_name='ManuallyUpdatedParticleProperty',
                     dtype='int32',
                     initial_value=0,
                     name=info['entry_count_prop'],
                     write=False)

    def initial_setup(self, **kwargs):

        info  = self.info
        params = self.params
        if params['update_interval'] is not None:
            si.msg_logger.msg('Can not set residence times update interval, as must equal time step',
                              fatal_error=True, hint= 'remove update_interval parameter for this class', caller = self)
        params['update_interval'] = si.settings.time_step

        # do standard stats initialize with schedular
        super().initial_setup()


        dm = si.dim_names
        info['count_dims']= {
                        dm.time: si.run_info.times.size,
                        dm.release_group:len(si.class_roles.release_groups)}

        # create count, residence time sumation buffers
        s=[ info['count_dims'][dm.time], info['count_dims'][dm.release_group]]
        self.sum_residence_age = np.full(s, 0., np.float64)
        self.count_residence_age  = np.full(s, 0, np.int64)
        self.sum_exposure_time =  self.sum_residence_time.copy()
        self.count_exposure_time = self.count_residence_time.copy()

        self.count = np.full(s, 0, np.int32)
        self.count_all_alive_particles = self.count.copy()
        self.entry_counts = self.count.copy()
        pass
    def open_output_file(self,file_name):
        nc = super().open_output_file(file_name)
        # write everything at the end
        return nc


    def do_counts(self,n_time_step, time_sec, sel, alive):
        params = self.params
        info = self.info
        nWrite = self.nWrites
        part_prop = si.class_roles.particle_properties
        stats_util._count_all_alive_time(part_prop['status'].data,
                                         part_prop['IDrelease_group'].data,
                                         self.count_all_alive_particles[nWrite,:],
                                         alive)
        # manual update which polygon particles are inside
        was_inside  = part_prop[info['was_inside_polygon_prop']]
        inside = part_prop[info['inside_polygon_prop']]
        was_inside.copy(info['inside_polygon_prop'],sel) # recode which polyon they were inside
        inside.update(n_time_step, time_sec, sel)

        # manual update of residence times
        self._sum_residence_times(time_sec,params['update_interval'], # interval is time step
                was_inside.data,
                inside.data,
                part_prop['IDrelease_group'].data,
                part_prop[info['first_entry_time_prop']].data, part_prop[info['entry_count_prop']].data,
                self.sum_residence_age[nWrite,:], self.count_residence_age[nWrite, :],
                self.sum_exposure_time[nWrite, :], self.count_exposure_time[nWrite, :],
                self.count[nWrite,:],
                self.entry_counts[nWrite, :],
                sel)


    @staticmethod
    @njitOT
    def _sum_residence_times(time, time_step, was_inside,inside,
                                IDrelease_group,
                                first_entry_time, entry_count,
                                sum_residence_age, count_residence_age,
                                sum_exposure_time, count_exposure_time,
                                count,entry_counts,
                                sel):
        # count selected particles, ie depth range, statuses selected ,water depth range
        for n in sel:
            ng = IDrelease_group[n]
            count[ng] += 1 # count all selected particles

            if inside[n] >= 0:
                # currently inside
                # count all time inside
                sum_exposure_time[ng] += time_step
                count_exposure_time[ng] += 1

                if was_inside[n] < 0 :
                    # has just entered
                    entry_count[n] += 1
                    if entry_count[n] == 1: first_entry_time[n] = time # note fist entry time t0

                if entry_count[n] == 1:
                    sum_residence_age[ng] += time_step
                    count_residence_age[ng] += 1

            elif inside[n] < 0 and was_inside[n] >= 0:
                # has just exited
                # transit time
                pass


    def info_to_write_on_file_close(self,nc):
        # write all data at the end
        dim_names = stats_util.get_dim_names(self.info['count_dims'])

        nc.write_variable('sum_residence_time', self.sum_residence_time,
                          dim_names, dtype=np.float64,
                          compression_level=si.settings.NCDF_compression_level, units='s',
                          description='Sum of strict residence times for each release group')
        nc.write_variable('count_residence_time', self.count_residence_time,
                          dim_names, dtype=np.int64,
                          description='Count of particles in sum_residence_time',
                          compression_level=si.settings.NCDF_compression_level)

        nc.write_variable('residence_time', self.sum_residence_time/self.count_residence_time,
                        dim_names, dtype=np.float64,
                        compression_level=si.settings.NCDF_compression_level, units='s',
                        description='Strict average residence time, i.e. time particles inside during first entry of polygon, for each release group. is = sum_residence_time/count_residence_time')

        nc.write_variable('sum_exposure_time', self.sum_exposure_time,
                          dim_names, dtype=np.float64,
                          compression_level=si.settings.NCDF_compression_level, units='s',
                          description='Sum of exposure times for each release group')
        nc.write_variable('count_exposure_time', self.count_exposure_time,  dim_names, dtype=np.int64,
                          description='Count of particles in sum_exposure_time',
                          compression_level=si.settings.NCDF_compression_level)
        nc.write_variable('exposure_time', self.sum_exposure_time/self.count_exposure_time,
                        dim_names, dtype=np.float64,
                        compression_level=si.settings.NCDF_compression_level, units='s',
                        description='Average exposure time, i.e. total time particles inside polygon, for each release group. is = sum_exposure_time/count_exposure_time')

        nc.write_variable('count', self.count,
                          dim_names, dtype=np.int32,
                          compression_level=si.settings.NCDF_compression_level,
                          description='Counts inside and outside polygon for any user depth/status restrictions, is alive, stationary, on bottom, stranded, or moving , z_min/z_max etc')
        nc.write_variable('count_all_alive_particles', self.count_all_alive_particles,
                          dim_names, dtype=np.int32,
                          compression_level=si.settings.NCDF_compression_level,
                          description='Count all partices inside and outside polygon which are stationary, on bottom, stranded, or  moving ')

        # write number released
        release_groups = si.class_roles.release_groups
        num_released = np.full((self.info['count_dims'][si.dim_names.release_group],),0, dtype=np.int32)
        for nrg, rg in enumerate(release_groups.values()):
            num_released[nrg] = rg.info['number_released']
        nc.write_variable('number_released', num_released,
                          dim_names[1], dtype=np.int32,
                          compression_level=si.settings.NCDF_compression_level,
                          description='Total particles released by each release group')

        pass


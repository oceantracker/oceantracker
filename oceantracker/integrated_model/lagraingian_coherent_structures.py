import numpy as np
from os import path
from oceantracker.util.numba_util import njitOT
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.integrated_model._base_model import  _BaseModel
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC
from oceantracker.util import time_util

from oceantracker.shared_info import SharedInfo as si

class LagarangianCoherentStructuresFTLEheatmaps2D(_BaseModel):
    # random polygon release in 2D or 3D
    #todo make work with lat lng

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params({
            'start_date': PVC(None, 'iso8601date', doc_str='start date of LSC calculation, Must be an ISO date as string eg. "2017-01-01T00:30:00" '),
            'end_date': PVC(None, 'iso8601date', doc_str=' end date of LSC calculation, Must be an ISO date as string eg. "2017-01-01T00:30:00"'),
            'update_interval': PVC(60*60.,float,units='sec',
                                    doc_str='Time in seconds between calculating statistics, will be rounded to be a multiple of the particle tracking time step'),
            'lags': PLC(None, [float,int], units='sec',min=1,
                        doc_str='List of one or more times after particle release to calculate Lagarangian Coherent Structures, default is 1 day'),
            'grid_size':           PLC([100, 99],[int], fixed_len=2,  min=1, max=10 ** 5,
                                            doc_str='number of rows and columns in grid'),
            'grid_center': PCC(None, one_or_more_points=True, is3D=False, doc_str='center of the grid release  (x,y) or (lon, lat) if hydromodel in geographic coords.', units='meters or decimal degrees'),
            'grid_span': PCC(None, one_or_more_points=True, min=1., is3D=False, doc_str='(width, height)  of the grid release, must be > 0.', units='meters or decimal degrees'),
            'floating': PVC(True, bool, doc_str='Particles will float at free surface if a 3D model'),
            'z_min': PVC(None, float, doc_str=' Only allow particles to be above this vertical position', units='meters above mean water level, so is < 0 at depth'),
            'z_max': PVC(None, float, doc_str=' Only allow particles to be below this vertical position', units='meters above mean water level, so is < 0 at depth'),
            'output_file_tag': PVC('LCS', str, doc_str='tag on output file'),
            'write_intermediate_results': PVC(False, bool, doc_str='write intermediate arrays, x_lag, strain_matrix. Useful for checking results'),
            'write_tracks':             PVC(False, bool, doc_str='Flag if "True" will write particle tracks to disk. This is off oby default for LCS'),
        })
        self.class_doc('Time series of Lagrangian Coherent Structures heat maps, calculated as Finite-Time Lyapunov exponents (FTLEs) at given lag times, see Haller, G., 2015. Lagrangian coherent structures. Annual review of fluid mechanics, 47, pp.137-162.')

    def add_settings_and_class_params(self):
        # change parameters
        info = self.info
        params = self.params

        # turn off dispersion
        self.settings(include_dispersion=False)

        # make a grid release group at each time interval and grid
        self.clear_class_role('release_groups') # cannot use with other releases

        # checks on params
        if params['grid_center'].shape[0] != params['grid_span'].shape[0]:
            si.msg_logger.msg('Grid span must be list of size [2] or be N pairs of sizes, one gor each grid center',
                              hint=f'Grid center has {params["grid_center"].shape[0]} values  and grid span is size  {str(params["grid_span"].shape)}',
                          fatal_error=True, exit_now=True, caller=self)

        release_params = dict(class_name='oceantracker.release_groups.grid_release.GridRelease',
                              pulse_size=1, z_min=params['z_min'], z_max=params['z_max'],
                              grid_size=params['grid_size'],
                              max_age = params['lags'][-1],  # run each to largest lag
                              release_interval=0.  )
        # if 3D sort out depth range and always resuspend
        if si.is3D_run:
            self.add_class('resuspension', critical_friction_velocity=0.0)  # always resuspend
            if params['floating']:
                self.add_class('trajectory_modifiers',
                               name='floater',class_name='SurfaceFloat')
            else:
                si.msg_logger.msg('LCS not yet working for non-floating particles',
                                  fatal_error=True, exit_now=True,caller=self)
        # get time for releases
        a = si.get_regular_events_within_hindcast(params['update_interval'], caller=self,
                    start=params['start_date'],end=params['end_date'],crumbs='LCS add_settings_and_class_params : ')
        info.update(a)
        for n_grid in range(params['grid_center'].shape[0]):
            release_params['grid_center'] = params['grid_center'][n_grid]
            release_params['grid_span'] = params['grid_span'][n_grid]

            for n_pulse in range(info['times'].size):
                release_params['release_start_date'] = time_util.seconds_to_isostr(info['times'][n_pulse])
                release_params['user_instance_info'] = (n_grid, n_pulse) # tag with grid and pulse number
                # add param dict as keyword arguments

                self.add_class('release_groups', name= f'LCS_grid{n_grid:03d}_time_step{n_pulse:04d}', **release_params )
                pass

    def initial_setup(self):
        params = self.params

        if si. hydro_model_cords_in_lat_long:
            si.msg_logger.msg(' to do LCS not yet working for hydro models ',fatal_error=True, exit_now=True)

        if params['lags'] is None: params['lags']  = [24*3600.]
        params['lags'] = np.asarray(params['lags']) # easier as an array
        r, c = params['grid_size']

        # grid release builds
        # set up space to hold release grids
        self.x_release_grids = np.full((params['grid_center'].shape[0], r, c, 2), np.nan, dtype=np.float64)

        # add lag schedular
        time = []
        for name, rg in si.roles.release_groups.items():
            # time of lags after start of release group
            t = rg.release_scheduler.info['start_time'] + params['lags']
            si.add_scheduler_to_class('LCScalculation_scheduler', rg, times= t,  caller=self, crumbs='Adding LCS calculation scheduler ')
            rg.info['next_lag_to_calculate'] = 0 # counter for the lag to work on

            # from first grid record start time of each pulse, as is the same for all grids
            n_grid, n_pulse = rg.params['user_instance_info']
            if n_grid == 0:  # first grid
                time.append(rg.LCScalculation_scheduler.info['start_time']) # record start time of each pulse, is the same for all grids

            # record grid from first pulse of each grid
            if n_pulse == 0:
                self.x_release_grids[n_grid, ...] = rg.info['x_grid']

        self.time= np.asarray(time) # times or t0 for LSC

        # add working space arrays
        n_lags = params['lags'].size
        self.x_at_lag= np.full((r,c,2), np.nan, dtype=np.float64) # locations grid aftr lag time
        self.LCS = np.full((r-1, c-1), np.nan, dtype=np.float64)

        self._open_output_file()

    def update(self, n_time_step, time_sec):
        part_prop = si.roles.particle_properties

        # do LSC calculation on schedule
        for n, rg in enumerate(si.roles.release_groups.values()):
             if rg.LCScalculation_scheduler.do_task(n_time_step):
                # find particles in this release group to do calculations at this lag
                sel = part_prop['IDrelease_group'].compare_all_to_a_value('eq', rg.info['IDrelease_group'], out=self.get_partID_buffer('ID1'))

                n_grid, n_pulse = rg.params['user_instance_info']

                self._calculate_LCS(n_pulse, n_grid, rg.info['next_lag_to_calculate'],  sel)

                rg.info['next_lag_to_calculate'] += 1
                pass
        pass

    def _calculate_LCS(self, n_pulse ,n_grid, n_lag, sel):
        params = self.params
        nc = self.nc
        part_prop = si.roles.particle_properties

        # make grid of current locations
        self.x_at_lag.fill(np.nan)
        self._get_locations_at_lag(part_prop['x'].data,
                                   part_prop['grid_release_row_col'].data,
                                    self.x_at_lag, sel)
        if np.all(np.isnan( self.x_at_lag)):
            pass
        #self.x_at_lag = self.x_at_lag - self.x_release_grids[n_grid, ...]  # converts x's into displacements

        # get LSC
        self.LCS.fill(np.nan)
        self._calc_LCS(self.x_release_grids[n_grid, :, :], self.x_at_lag, self.LCS)
        self.LCS = np.log(np.sqrt(self.LCS))/params['lags'][n_lag]

        #write LSCs
        nc.file_handle.variables['LCS'][n_pulse, n_grid, n_lag, ...] = self.LCS

        if params['write_intermediate_results']:
            nc.file_handle.variables['x_at_lag'][n_pulse, n_grid, n_lag, ...] = self.x_at_lag
        pass

    def _open_output_file(self):

        params = self.params
        self.info['output_file'] = si.output_file_base + '_' + self.params['output_file_tag'] + '.nc'
        self.nc = NetCDFhandler(path.join(si.run_output_dir, self.info['output_file']), 'w')
        nc = self. nc

        nc.add_dimension('time_dim', None) # open time dim
        nc.add_dimension('lag_dim', params['lags'].size)
        nc.add_dimension('release_grid_rows', self.x_at_lag.shape[0])
        nc.add_dimension('release_grid_cols', self.x_at_lag.shape[1])
        nc.add_dimension('grid_dim',  params['grid_center'].shape[0])
        nc.add_dimension('vector2D', 2)
        nc.add_dimension('rows', self.LCS.shape[0])
        nc.add_dimension('cols', self.LCS.shape[1])

        # write release group
        nc.write_a_new_variable('time', self.time,'time_dim', dtype=np.float64,
                                description='Time, or start time for calculation of Finite-Time Lyapunov exponents (FTLEs) type LCS',
                                attributes=dict(units='seconds since 1/1/1970'))
        nc.write_a_new_variable('lags', params['lags'], 'lag_dim', dtype=np.float64,
                                description='Lags between release and calculation of FTLEs  type LCS',
                                attributes=dict(units='seconds'))

        nc.write_a_new_variable('x_release_grid', self.x_release_grids,
                                ['grid_dim', 'release_grid_rows', 'release_grid_cols','vector2D'],
                             description='x,y locations of grid release',
                             attributes=dict(units='meters or longitude deg.'))
        nc.create_a_variable('LCS', ['time_dim', 'grid_dim', 'lag_dim', 'rows', 'cols'],
                             self.x_at_lag.dtype, description=' Largest Eigen value of 2D strain matrix', fill_value=np.nan,
                             attributes=dict(units='dimensionless'))

        # optional output
        if params['write_intermediate_results']:
            nc.create_a_variable('x_at_lag',['time_dim','grid_dim', 'lag_dim','release_grid_rows','release_grid_cols','vector2D'],
                             self.x_at_lag.dtype, description='x,y locations of particles at given lags', fill_value=np.nan,
                             attributes=dict(units='meters or (lon, lat)  deg.') )

    @staticmethod
    @njitOT
    def _get_locations_at_lag(x, row_col_part_prop, x_at_lag, sel):
        # insert current location into original grid
        # loop over particles in this release group
        #todo only for moving particles?
        for n in sel:
            r, c = row_col_part_prop[n] # row and column at release
            for m in range(2):
                x_at_lag[r, c, m ] = x[n,m]

    @staticmethod
    @njitOT
    def _calc_LCS(x_release_grid, x_at_lag, LCS):
        #  find strain marix foy each grid point at the center of the release grid cells
        #  LSC is largest eigen value of this matrix
        F_deformation_grad =  np.full((2,2),0.,dtype=np.float64)
        C_strain_tensor = np.full((2, 2), 0., dtype=np.float64)
        e_vals = np.full((2,), 0., dtype=np.float64)

        # initial  equal separations
        dx0=  x_release_grid[0, 1, 0] - x_release_grid[0, 0, 0]
        dy0 = x_release_grid[1, 0, 1] - x_release_grid[0, 0, 1]

        for r in range(x_release_grid.shape[0] - 1):
            for c in range(x_release_grid.shape[1] - 1):
                for n in range(2):
                    # x grads strain in, first column
                    F_deformation_grad[n, 0]  = 0.5 * (x_at_lag[r, c+1, n] + x_at_lag[r+1, c+1, n])
                    F_deformation_grad[n, 0] -= 0.5 * (x_at_lag[r, c  , n] + x_at_lag[r+1, c  , n])
                    F_deformation_grad[n, 0] /= dx0  # divide by initial separation
                    # x grads strain in, second column
                    F_deformation_grad[n, 1]  = 0.5 * (x_at_lag[r+1, c, n] + x_at_lag[r+1, c+1, n])
                    F_deformation_grad[n, 1] -= 0.5 * (x_at_lag[r  , c, n] + x_at_lag[r  , c+1, n])
                    F_deformation_grad[n, 1] /= dy0 # divide by initial separation

                C_strain_tensor[:] = F_deformation_grad.T* F_deformation_grad

                eigen_vals2by2(C_strain_tensor, e_vals)

                LCS[r, c] = e_vals[0] if abs(e_vals[0]) >= abs(e_vals[1]) else e_vals[1]
        pass



    def close(self):
        self.nc.close()

@njitOT
def eigen_vals2by2(A, e_vals):
    # Trace and Determinant of matrix
    T = A[0, 0] + A[1, 1]
    D = A[0, 0] * A[1, 1] - A[0, 1] * A[0, 1]

    # get Eigen values as  get solutions to a quadratic eq.
    r = np.sqrt(T ** 2 - 4.0 * D)
    e_vals[0] = 0.5 * (T - r)
    e_vals[1] = 0.5 * (T + r)

import numpy as np
from os import path
from oceantracker.util.numba_util import njitOT
from oceantracker.util.ncdf_util import NetCDFhandler
from oceantracker.integrated_model._base_model import  _BaseIntegratedModel
from oceantracker.util.parameter_checking import ParameterListChecker as PLC, ParamValueChecker as PVC, ParameterCoordsChecker as PCC, ParameterTimeChecker as PTC
#from oceantracker.util.parameter_checking import ParameterListCheckerV2 as PLC2
from oceantracker.util import time_util
from copy import  deepcopy
from oceantracker.shared_info import shared_info as si

class dev_LagarangianStructuresFTLE2D(_BaseIntegratedModel):
    '''Time series of Lagrangian Coherent Structures heat maps,
     calculated as Finite-Time Lyapunov exponents (FTLEs) at given lag times,
     see Haller, G., 2015. Lagrangian coherent structures.
     Annual review of fluid mechanics, 47, pp.137-162.')
     Currently only 2D  implemented
     '''

    def __init__(self):
        # set up info/attributes
        super().__init__()
        self.add_default_params(
            start=  PTC(None, doc_str='start date of LSC releases, Must be an ISO date as string eg. "2017-01-01T00:30:00" '),
            end=  PTC(None, doc_str=' end date of LSC releases. Model should run max(lags) beyond this send date to calculate LSC for last pulse of grid release.  Must be an ISO date as string eg. "2017-01-01T00:30:00"'),
            release_interval=  PVC(3600.,float,units='sec',min=0.,
                        doc_str='Time in seconds between grid releases of pulses of particles. For each pulse an LCS will be calculated at the given lag times. This creates a LCS time series for each lag at this time interval'),
            lags=  PLC(None, float, units='sec',min=1,min_len=1,
                        is_required=True,
                        doc_str='List of one or more times after each pulse is released to calculate LCS.'),
            grid_size=  PLC([100, 99],int, fixed_len=2,  min=1, max=10 ** 5,
                                            doc_str='number of rows and columns in grid'),
            grid_center=  PCC(None, one_or_more_points=True, is3D=False,is_required=True,
                               doc_str='center of one or more LCS grid centers  or (lon, lat) if hydromodel in geographic coords., should be [x,y] or [[x1,y1],[x1,y1],...] for multiple grids, which may have different spans, but all must have same number of rows and columns ',
                              units='meters or decimal degrees'),
            grid_span=  PCC(None, one_or_more_points=True, min=.0001, is3D=False, is_required=True,
                             doc_str='(width, height)  of the grid release, should be single [dx,dy] or [[dx1,dy1],[dx1,dy1],...] with one pair for each grid center', units='meters only'),
            floating=PVC(True, bool, doc_str='Do LCS for floating partyicles, in development currently only option '),
            z_min=  PVC(None, float, doc_str=' Only allow particles to be above this vertical position', units='meters above mean water level, so is < 0 at depth'),
            z_max=  PVC(None, float, doc_str=' Only allow particles to be below this vertical position', units='meters above mean water level, so is < 0 at depth'),
            output_file_tag=  PVC('LCS', str, doc_str='tag on output file'),
            backwards=  PVC(False, bool, doc_str='Do LCS backwards in time'),
            write_intermediate_results=  PVC(False, bool, doc_str='write intermediate arrays, x_lag, strain_matrix. Useful for checking results'),
            write_tracks=  PVC(False, bool, doc_str='Flag if "True" will write particle tracks to disk. This is off by default for LCS'),

        )
    def add_required_classes_and_settings(self, settings, reader_builder, msg_logger):
        info = self.info
        # change parameters
        info = self.info
        params = self.params
        params['lags'] = np.asarray(params['lags'] )
        # turn off dispersion
        si.settings.use_dispersion = False
        #, backtracking= params['backwards'])and ste forrad/mackwads

        # make a grid release group at each time interval and grid
        # clear existing releases
        si.class_roles.release_groups={} # not use with other releases

        # checks on params
        if params['grid_center'].shape[0] != params['grid_span'].shape[0]:
            si.msg_logger.msg('Grid span must be list of size [2] or be N pairs of sizes, one gor each grid center',
                              hint=f'Grid center has {params["grid_center"].shape[0]} values  and grid span is size  {str(params["grid_span"].shape)}',
                          fatal_error=True, exit_now=True, caller=self)

        si.msg_logger.exit_if_prior_errors('LSC error??', caller=self)
        # set up lCS grid
        r, c = params['grid_size']

        # set up release grid is padded by one all around
        release_params = dict(class_name='oceantracker.release_groups.grid_release.GridRelease',
                              pulse_size=1,
                              z_min=params['z_min'], z_max=params['z_max'],
                              grid_size= [r+2, c+2],
                              max_age = params['lags'][-1],  # run each to largest lag
                              release_interval=0. )
        # if 3D sort out depth range and always resuspend
        if si.run_info.is3D_run:
            if params['floating']:
                si.add_class('trajectory_modifiers',name='floater',class_name='SurfaceFloat')
            else:
                si.msg_logger.msg('LCS not yet working for non-floating particles', fatal_error=True, exit_now=True,caller=self)

        # get time for pulse releases within hindcast
        fgm = si.core_class_roles.field_group_manager
        if params['start'] is None: params['start'] = fgm.info['end_time'] if si.settings.backtracking else fgm.info['start_time']
        if params['end']   is None: params['end']   = fgm.info['start_time'] if si.settings.backtracking else fgm.info['end_time']
        params['release_interval'] = round(params['release_interval']/si.settings.time_step,0 )*si.settings.time_step

        duration = abs(params['end']-params['start'])
        info['times']= params['start'] + si.run_info.model_direction * np.arange(0, duration - params['lags'].max() + params['release_interval'] , params['release_interval'] )
        if info['times'].size ==0:
            si.msg_logger.msg('LSC/FTLE model duration is less than largest requested lag', hint=f'Check hindcast duration, or start end parameters lags={str(params["lags"])}',
                              crumbs='Setting up release times', caller=self,fatal_error=True, exit_now=True)

        sel = np.logical_and(info['times'] >= fgm.info['start_time'],info['times'] <= fgm.info['end_time'], )
        info['times'] =  info['times'][sel]

        # set up release group for each pulse
        for n_grid in range(params['grid_center'].shape[0]):
            rp = deepcopy(release_params)
            rp['grid_center'] = params['grid_center'][n_grid]
            rp['grid_span'] = params['grid_span'][n_grid]

            for n_pulse in range(info['times'].size):
                rp['start'] = info['times'][n_pulse]
                # add param dict as keyword arguments, must not initialize yet, ie delay initial_setup till al release groups added
                si.add_class('release_groups', name= f'LCS_grid_{n_grid:03d}_pulse_{n_pulse:04d}', **rp, initialize=False)
            pass

    def initial_setup(self):
        params = self.params

        
        if si. hydro_model_cords_in_lat_long:
            si.msg_logger.msg(' to do LCS not yet working for lon-lat hydro models ',fatal_error=True, exit_now=True)

        if params['lags'] is None: params['lags']  = [24*3600.]
        params['lags'] = np.asarray(params['lags']) # easier as an array
        r, c = params['grid_size']

        # grid release builds
        # set up space to hold release grids
        self.x_release_grids = np.full((params['grid_center'].shape[0], r+2, c+2, 2), np.nan, dtype=np.float64)
        self.x_LSC_grid = np.full((params['grid_center'].shape[0], r , c , 2), np.nan, dtype=np.float64)
        # add lag schedular
        time = []
        md = si.run_info.model_direction

        for name, rg in si.class_roles.release_groups.items():
            # time of lags after start of release group
            t = rg.schedulers['release'].info['start_time'] + md*params['lags']

            rg.add_scheduler('LCScalculation_scheduler', times=t, caller=self, crumbs=f'Adding LCS calculation scheduler release group "{name}" ')
            rg.info['next_lag_to_calculate'] = 0 # counter for the lag to work on

            # from get grid and pulse ID from the release group name
            s = name.split('_')
            rg.info['n_grid'],rg.info['n_pulse'] = int(s[2]), int(s[4])

            if rg.info['n_grid'] == 0:  # first grid
                time.append(rg.schedulers['LCScalculation_scheduler'].info['start_time']) # record start time of each pulse, is the same for all grids

            # record grid from first pulse of each grid
            if rg.info['n_pulse'] == 0:
                self.x_release_grids[rg.info['n_grid'], ...] = rg.info['x_grid']
                self.x_LSC_grid[rg.info['n_grid'], ...] = rg.info['x_grid'][1:-1,1:-1,:]

        self.time= np.asarray(time) # times or t0 for LSC

        # add working space arrays
        self.x_at_lag=  np.full((r+2, c+2, 2), np.nan, dtype=np.float64)
        self.FTLE  = np.full((r, c), np.nan, dtype=np.float64)
        self.eigen_values = np.full((r, c, 2), np.nan, dtype=np.float64)
        self.eigen_vectors = np.full((r, c, 2, 2), np.nan, dtype=np.float64)
        self._open_output_file()

    def update(self, n_time_step, time_sec):
        part_prop = si.class_roles.particle_properties

        # do LSC calculation on schedule
        for n, rg in enumerate(si.class_roles.release_groups.values()):
             if rg.schedulers['LCScalculation_scheduler'].do_task(n_time_step):
                # find particles in this release group to do calculations at this lag
                sel = part_prop['IDrelease_group'].compare_all_to_a_value('eq', rg.info['IDrelease_group'], out=self.get_partID_buffer('ID1'))

                self._calculate_LCS(rg.info['n_pulse'],rg.info['n_grid'], rg.info['next_lag_to_calculate'],  sel)
                rg.info['next_lag_to_calculate'] += 1
                pass
        pass

    def _calculate_LCS(self, n_pulse ,n_grid, n_lag, sel):
        params = self.params

        part_prop = si.class_roles.particle_properties

        # make grid of current locations
        self.x_at_lag.fill(np.nan)
        self._get_locations_at_lag(part_prop['x'].data,
                                   part_prop['grid_release_row_col'].data,
                                    self.x_at_lag, sel)

        # get LSC, first fil matrcies with nan to blank areas outside domain, or dry
        self.FTLE.fill(np.nan)
        self.eigen_values.fill(np.nan)
        self.eigen_vectors.fill(np.nan)

        self._calc_FTLE(self.x_release_grids[n_grid, :, :], self.x_at_lag, self.FTLE, self.eigen_values, self.eigen_vectors)

        self.FTLE = np.log(np.sqrt(self.FTLE)) / params['lags'][n_lag]

        #write LSCs
        nc = self.nc
        nc.file_handle.variables['FTLE'][n_pulse, n_grid, n_lag, ...] = self.FTLE
        nc.file_handle.variables['eigen_values'][n_pulse, n_grid, n_lag, ...] = self.eigen_values
        nc.file_handle.variables['eigen_vectors'][n_pulse, n_grid, n_lag, ...] = self.eigen_vectors

        if params['write_intermediate_results']:
            nc.file_handle.variables['x_at_lag'][n_pulse, n_grid, n_lag, ...] = self.x_at_lag
        pass

    def _open_output_file(self):

        params = self.params
        self.info['output_file'] = si.run_info.output_file_base + '_' + self.params['output_file_tag'] + '.nc'
        self.nc = NetCDFhandler(path.join(si.run_info.run_output_dir, self.info['output_file']), 'w')
        nc = self. nc
        r, c = params['grid_size']
        nc.add_dimension('time_dim', None) # open time dim
        nc.add_dimension('lag_dim', params['lags'].size)
        nc.add_dimension('release_grid_rows', r+2)
        nc.add_dimension('release_grid_cols', c+2)
        nc.add_dimension('grid_dim',  params['grid_center'].shape[0])
        nc.add_dimension('vector2D', 2)
        nc.add_dimension('rows', r)
        nc.add_dimension('cols', c)

        # write release group
        nc.write_a_new_variable('time', self.time,'time_dim', dtype=np.float64,
                                description='Time, or start time for calculation of Finite-Time Lyapunov exponents (FTLEs) type LCS',
                                attributes=dict(units='seconds since 1/1/1970'))
        nc.write_a_new_variable('lags', params['lags'], 'lag_dim', dtype=np.float64,
                                description='Lags between release and calculation of FTLEs  type LCS',
                                attributes=dict(units='seconds'))

        nc.write_a_new_variable('x_LSC_grid', self.x_LSC_grid,
                                ['grid_dim', 'rows', 'cols','vector2D'],
                             description='x,y locations of calculationed LCS',
                             attributes=dict(units='meters or longitude deg.'))


        nc.create_a_variable('FTLE', ['time_dim', 'grid_dim', 'lag_dim', 'rows', 'cols'],
                             np.float32, description=' Largest Eigen value of 2D strain matrix', fill_value=np.nan,
                             attributes=dict(units='dimensionless'))
        nc.create_a_variable('eigen_values', ['time_dim', 'grid_dim', 'lag_dim', 'rows', 'cols','vector2D'],
                             np.float32, description='Eigen values of 2D strain matrix, largest first', fill_value=np.nan,
                             attributes=dict(units='dimensionless'))
        nc.create_a_variable('eigen_vectors', ['time_dim', 'grid_dim', 'lag_dim', 'rows', 'cols', 'vector2D', 'vector2D'],
                             np.float32, description='Columns are Eigen vectors of 2D strain matrix, vector for largest eigen value in the first column t', fill_value=np.nan,
                             attributes=dict(units='dimensionless'))

        # optional output
        if params['write_intermediate_results']:
            nc.write_a_new_variable('x_release_grid', self.x_release_grids,
                                    ['grid_dim', 'release_grid_rows', 'release_grid_cols', 'vector2D'],
                                    description='x,y locations of grid release',
                                    attributes=dict(units='meters or longitude deg.'))
            nc.create_a_variable('x_at_lag',['time_dim','grid_dim', 'lag_dim','release_grid_rows','release_grid_cols','vector2D'],
                             np.float32, description='x,y locations of particles at given lags', fill_value=np.nan,
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
    def _calc_FTLE(x_release_grid, x_at_lag, FTLE, eigen_values, eigen_vectors):
        #  find strain marix foy each grid point at the center of the release grid cells
        #  LSC is largest eigen value of this matrix

        # working space
        F_deformation_grad =  np.full((2,2),0.,dtype=np.float64)
        C_strain_tensor = np.full((2, 2), 0., dtype=np.float64)
        e_val = np.full((2, ), 0., dtype=np.float64)
        e_vec = np.full((2,2), 0., dtype=np.float64)

        # initial  equal separations
        dx0=  x_release_grid[0, 1, 0] - x_release_grid[0, 0, 0]
        dy0 = x_release_grid[1, 0, 1] - x_release_grid[0, 0, 1]

        for r in range(1,x_release_grid.shape[0] - 1):
            for c in range(1, x_release_grid.shape[1] - 1):
                for m in range(2):
                    # x grads strain in, first column
                    F_deformation_grad[m, 0]  = (x_at_lag[r, c+1, m] - x_at_lag[r, c-1, m])/2.0/dx0
                    # y grads strain in, second column
                    F_deformation_grad[m, 1] = (x_at_lag[r+1, c , m] - x_at_lag[r - 1, c, m]) / 2.0 / dy0
                # don't calculate if any grid relesed outside domain or by default in dry cells
                if np.any(np.isnan(F_deformation_grad)) : continue

                C_strain_tensor[:] = np.dot(F_deformation_grad.T, F_deformation_grad)
                e_val[:], e_vec[:] = np.linalg.eig(C_strain_tensor)

                # put largest  eigen value first
                n1 = int(abs(e_val[1]) >= abs(e_val[0])) # largest value index
                n2 = (n1 + 1) % 2 # other index
                r1, c1 = r - 1, c - 1
                eigen_values[r1, c1, 0],   eigen_values[r1, c1, 1] = e_val[n1], e_val[n2]
                eigen_vectors[r1, c1, :, 0],   eigen_vectors[r1, c1, :, 1] = e_vec[:, n1], e_vec[:, n2]
                FTLE[r1, c1] = eigen_values[r1, c1, 0] #largest
        pass

    def close(self):
        self.nc.close()


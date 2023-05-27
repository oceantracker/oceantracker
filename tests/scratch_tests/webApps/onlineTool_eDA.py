# eDNA particle tracker in pure python
# uses particle backtracking to build eDNA dection maps for harbour sites
# Ross Vennell sept 2021
# releases particles at 15min inervals for in 1hr windows around given release location and times
#

import numpy as np
import oceantracker.util.dev.OTreRunner as OTreRunner
from time import  perf_counter
from oceantracker.util import time_util
from datetime import datetime
from copy import deepcopy
from  oceantracker.util.cord_transforms import NZTM_to_WGS84, WGS84_to_NZTM
import matplotlib.pyplot as plt


def get_base_params():

    params = {  'shared_params': {
                                  'root_output_dir': 'test',
                                  'output_file_base': None,
                                  'write_case_info': False,
                                  'debug' : True,
                                   'max_duration' : 6*24*3600,
                                  },
                'reader': {'class_name': 'oceantracker.reader.generic_ncdf_readerUnstructured.GenericReaderNCDF','input_dir':None,
                                        'water_velocity_map': {'u': 'u', 'v': 'v'},
                'field_map': {'water_depth': 'depth'},
                'dimension_map': {'node': 'node', 'time': 'time'},
                'grid_map': {'time': 'time', 'x': 'x', 'y': 'y', 'dry_cells': 'dry_cells','triangles': 'simplex'},
                'time_buffer_size': 24 * 4,
                'hindcast_date_of_time_zero': '1970-01-01',
                'file_mask': None},
                'base_case_params': {'run_params': {'backtracking': True,
                                                    'write_grid': False,
                                                    'write_tracks': False,
                                                    'write_log_file' : False,
                                                    'duration' : 3*24*3600.,

                                                    },
                                       'particle_group_manager': {},
                                       'tracks_writer': {'output_step_count': 3},
                                       'dispersion': {'A_H': 1.0},
                                        'particle_release_groups' :  [],

                                        'particle_properties': [
                                               {'class_name': 'oceantracker.particle_properties.age_decay.AgeDecay',
                                                'name': 'DNAdecay', 'initial_value': 1., 'decay_time_scale': 3*3600.}
                                               ],
                                           'particle_statistics': [
                                               {'class_name': 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_agedBased',
                                                'calculation_interval': 600, 'particle_property_list': ['DNAdecay','water_depth'],
                                                 #'release_group_centered_grids': True,
                                                 'grid_center': None,
                                                 'grid_span': [10000, 10000],
                                                 'grid_size': [290, 291],
                                                'min_age_to_bin': 0.,
                                                'write' : False,
                                                'max_age_to_bin': 1000*24*3600., 'age_bin_size':1000*24*3600.,
                                                }]}
                                      }

    release_template={  'points': None, 'release_start_date': None, 'pulse_size': None,
                       'release_interval': 900., 'release_duration': 3600.,
                       'maximum_age' : None,'release_radius' : 20,
                       'user_particle_property_parameters': { 'DNAdecay': {'initial_value' : 1.0}} }  # initial value may be + or - for detection/non-detection
    params['base_case_params']['particle_release_groups'] =[release_template]
    return params

def region_setup_params(regionID, test_root_output_dir=None):

    params=get_base_params()
    region_info={ 'max_release_points' : 6, 'max_decay_time_scale_hours' : 12,'max_time_afterHW_hours':12 }

    # defaults
    pulse_size= 300

    if regionID ==0:
        # opua bay of islands
        p = [1702000., 6091200.]
        twhightide=  [datetime(2020,10,27,4,19).isoformat(),
                     datetime(2020,10,30,7,3).isoformat(),
                     datetime(2020,11,1,20,55).isoformat()]

        output_file_base = 'Opua_eDNA_V1'
        file_mask ='eDNAtool_MPInorthland_v01.nc'

        # test release
        rg= { 'points':[p],'release_start_date':twhightide[1],
              'release_radius': 10., # make sample location fuzzy as sampling takes time
              'pulse_size' : pulse_size}
           # stats grid
        s = {'grid_span': [10000, 10000], 'grid_size': [290, 291], 'grid_center': p}
        ax= [1695800,  1708600,  6089100,  6100500]   # only used in test mode


    params['shared_params']['output_file_base'] = output_file_base
    params['reader']['file_mask']= file_mask
    case_params = params['base_case_params']
    pg = case_params['particle_release_groups'][0]
    pg.update(rg)

    max_part = int(region_info['max_release_points']*pulse_size* pg['release_duration']/pg['release_interval'] + 10)

    si.run_params.update({'particle_buffer_size': max_part})

    case_params['particle_statistics'][0].update(s)

    region_info['axes'] = ax
    region_info['test_point_NZTM'] = p
    region_info['test_point_WGS84'] = NZTM_to_WGS84(np.asarray([p])).tolist()
    region_info['high_tides'] = twhightide

    if test_root_output_dir is not None:
        params['shared_params'].update({'root_output_dir' : test_root_output_dir})
        case_params['run_params'].update({'write_grid': True, 'write_tracks': True,  'write_log_file' : True})
        case_params['particle_statistics'][0].update({'write': True})
    return params, region_info


class Online_eDNA(OTreRunner.OceanTrackerReRunner):
    tideID_map = {'neap tide': 0, 'mid range': 1, 'spring tide': 2}

    def __init__(self, pre_built_reader, emit_method, regionID):
        super(). __init__(pre_built_reader, emit_method)
        self.regionID = regionID

    def get_front_end_request_defaults(self):
        params, region_info = region_setup_params(self.regionID)

        front_end_request = {'regionID': self.regionID,
                            'tide_type': 'mid range',  # 'neap tide', 'mid range', 'spring tide'
                            'time_afterHW_hours' : 0.,  # 0-12hr,  time offset of all samples
                            'points_list_WGS84': [region_info['test_point_WGS84']],  # up to 6 points?
                            'decay_time_scale_hours': 3.,  # sablella

                             # these could be used to scale or clip values client side , but could be done server side
                             'number_of_animals': 1,  # number of animals shedding dna [1, 10, 100]
                             'DNA_shedding_rate_million_copies_perAdultAnimal_perHour': 20., # sabella
                             'detection_limit_copies_per_ml': 0.14,  # DNA copies per microliter of retained sample
                           # allow front user/auto grid sizing later?
                             'grid_span': 10000,
                             'grid_size': 290}
        return front_end_request

    def _get_engine_info(self):
        # add region info to model_info
        d={}
        params, region_info = region_setup_params(self.regionID)
        d['region_info'] = region_info
        return d

    def emit_engine_info(self):
        d = super()._get_engine_info()

        # convert outlines to lat/log
        for outline in d['grid_outline']:
            outline['points'] = NZTM_to_WGS84(outline['points'] )

        d.update(self._get_engine_info())
        self.emit('engine_info', d)

    def rerun(self,front_end_params= None, emit_method = OTreRunner.emit_to_print):

        if front_end_params is None:
            front_end_params = self.get_front_end_request_defaults()

        tideID= self.tideID_map[front_end_params['tide_type']]

        otsim = self.otsim
        si = otsim.shared_info
        case_params = si.working_params['case_params']

        rparams, region_info = region_setup_params(front_end_params['regionID'])
        self.response_start()
        # build new release groups
        pg_param=[]
        pNZTM=[]

        for p in front_end_params['points_list_WGS84']:
            pg = deepcopy(rparams['base_case_params']['particle_release_groups'][0])
            t0 = time_util.iso8601str_to_seconds(region_info['high_tides'][tideID]) + front_end_params['time_afterHW_hours'] * 3600.
            t0 += pg['release_duration']/2  # center particle rleases on given time
            p1= WGS84_to_NZTM(np.asarray(p)).tolist()
            pg.update({'points': p1,
                          'release_start_date': time_util.seconds_to_isostr(t0)
                          })

            pg_param.append(pg)

            pNZTM.append (p1[0]) # to get mean location

        case_params['particle_release_groups'] = pg_param

        case_params['particle_properties'][0]['decay_time_scale'] = front_end_params['decay_time_scale_hours']

        # run for 7 foldings
        case_params['run_params']['duration'] = 7. * abs(front_end_params['decay_time_scale_hours']) * 3600

        # change stats max age to bin based on duration, grid center etc
        # first adjust center of grid to mean of points
        si.user_classes['particle_statistics'][0].p.update({
            'grid_center': np.mean(np.asarray(pNZTM), axis=0).tolist()})

        self._do_a_rerun(case_params, emit_method)

        s=self.otsim.shared_info.user_classes['particle_statistics'][0]

        with np.errstate(divide='ignore', invalid='ignore'):
            count   = np.sum(s.count_time_slice[0], axis=0)
            unit_conc    = np.sum(s.sum_binned_part_prop['DNAdecay'][0],axis=0)/count
            depth   = np.sum(s.sum_binned_part_prop['water_depth'][0], axis=0)/count

            # Concetration based in cell area for depth averaged particle counts
            unit_conc = unit_conc / abs(depth) / s.grid['cell_area'] # concentration perm^3 based un unit initial value

        # get load per particle
        release_interval= case_params['particle_release_groups'][0]['release_interval']

        copies_per_sec = front_end_params['number_of_animals']*front_end_params['DNA_shedding_rate_million_copies_perAdultAnimal_perHour']*1.0E6/3600
        copies_per_particle = copies_per_sec*release_interval
        conc = unit_conc * count* copies_per_particle  # conc per grid cell of copies

        sampling_volume = abs(depth) * 0.05**2 # depth times area of sampler pulled through full water depth
        retained_sample_size_vol = 1000*1.E-6  # 1000ml retained sample in m^3
        detection_limit = front_end_params['detection_limit_copies_per_ml'] * 1.0E6 * sampling_volume/retained_sample_size_vol

        # mask below detection
        #conc[conc < detection_limit] = np.nan
        #np.sum((conc < detection_limit) & (conc != np.nan))
        # refs for test plots

        # take log but retain sign to allow for non-detections as -ve conc.
        conc = np.sign(conc)*np.log10(np.abs(conc))

        self.for_test_plot = {'count': count,'conc': conc, 'heat_map_grid': s.grid,
                              'model_grid': si.classes['interpolator'].grid,
                              }

        d= {    'boundsNZTM': { 'lower_left' : np.asarray([s.grid['x'][0, 0], s.grid['y'][0, 0] ]).tolist(),
                                'upper_right': np.asarray([s.grid['x'][0,-1], s.grid['y'][0, -1]]).tolist() },
                'boundsWGS84': {'lower_left': NZTM_to_WGS84( np.asarray([s.grid['x'][0,  0], s.grid['y'][0,  0]])).tolist(),
                                'upper_right':NZTM_to_WGS84( np.asarray([s.grid['x'][0, -1], s.grid['y'][0, -1]])).tolist()},
                'grid_size' : list(conc.shape),
                'log10Concentration' : conc.tolist(),
                'min': np.nanmin(conc),
                'max': np.nanmax(conc)
            }
        self.emit('DNAconcGrid',d)

        super().response_end()


if __name__ == '__main__':

    emit_method = OTreRunner.emit_to_print
    #emit_method = OTreRunner.no_emit

    #test_root_output_dir = None
    test_root_output_dir=   'F:/OceanTrackerOuput/Bio_toolBox/Northland2021'

    engines=[]

    # required hindcast dir location
    input_dir = 'F:\\HindcastReWrites\\oceantrackerFMT\\MPImetOceantrack\\northland\\2D'

    for regionID in [0]:

        # 1) pre build reader for this region
        params, region_info  = region_setup_params(regionID) # build run param with default params
        pre_built_reader = OTreRunner.build_reader(input_dir, params)

        t0 = perf_counter()

        # 2) Build engine for this region to get rerunaable class using prebuilt reader
        engine = Online_eDNA(pre_built_reader, emit_method, regionID)

        # 3) do first run to set up interp and compile numba code
        engine.first_run(params)

        print('Engine build time ', perf_counter()- t0 )
        t0 = perf_counter()

        #4) on front ends first intial contact send info about region eg outlines to mask areas to click on, test point etc
        engine.emit_engine_info()  # get regional info once for client, eg test point, default params etc

        engine.rerun() # use default front end request to draw test point heat map, use grid bounds to give initial view 15% larger?

        # 5) do use reruns on calcuate request, using  front end request values, max values are sent in  emit_engine_info emit
        front_end_request = {'regionID': regionID,
                            'tide_type': 'spring tide',  # tideID_map = {'neap tide': 0, 'mid range': 1, 'spring tide': 2}
                            'time_afterHW_hours' : 12.,  # 0-12hr,  time offset of all samples
                            'points_list_WGS84': [region_info['test_point_WGS84'], region_info['test_point_WGS84']],  # up to 6 points?
                            'decay_time_scale_hours': -3.,  # 1-12 hours
                             # these could be used to scale or clip values client side , but could be done server side
                             'detection_limit_copies_per_micro_litre' : 0.14,
                             'number_of_animals': 1,  # number of animals shedding dna [1, 10, 100]
                             'DNA_shedding_rate_million_copies_perAdultAnimal_perHour': 20,
                             'detection_limit_copies_per_ml': 0.14,#  DNA copies per ml
                            }
        engine.rerun(front_end_request,emit_method=OTreRunner.emit_to_print)

        print('Rerun time', perf_counter() - t0,'particles=', engine.otsim.shared_info.classes['particle_group_manager'].info['num_released'])

        engines.append(engine)

        # plot checks
        testplot = engine.for_test_plot
        z = testplot['conc']
        plt.pcolormesh(testplot['heat_map_grid']['x'][0, :], testplot['heat_map_grid']['y'][0, :], z , shading='gouraud', vmin=np.nanmin(z), vmax=np.nanmax(z))
        #plt.triplot( testplot['model_grid']['x'][:,1], testplot['model_grid']['x'][:,1], testplot['model_grid']['triangles'],color=(0.8, 0.8, 0.8))
        plt.show()

        # check plots
        '''
        if test_root_output_dir is not None:
            params, region_info = region_setup_params(regionID, test_root_output_dir=test_root_output_dir)
            params['reader'].update({'input_dir':input_dir })
            ot = OceanTrackerRunner()
            ot.run(params)

            runInfo_file_name=  path.join(params['shared_params']['root_output_dir'], params['shared_params']['output_file_base']+ '_runInfo.json')

            runCaseInfo= load_output_files.load_runCaseInfo(runInfo_file_name, ncase=0)

            ax=region_info['axes']

            particle_plot.animate_particles(runCaseInfo, axes=ax, text='Opua Tracks')
            particle_plot.plot_heat_map(runCaseInfo, axes=ax, text='Age based counts heat maps built on the fly, no tracks recorded',
                                    logscale=True,var='DNAdecay',   vmin=-3,  vmax=0 )

            particle_plot.plot_heat_map(runCaseInfo, axes=ax,
                                 text='Age based counts heat maps built on the fly, no tracks recorded',
                                  var='water_depth')
        '''

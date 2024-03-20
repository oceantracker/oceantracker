# allows rerun of single case from prebuilt reader held in memory
# if __name__ == '__main__': outlines steps to use it as a rerunner
import argparse
from datetime import datetime
from oceantracker.util import time_util
from oceantracker.shared_info import SharedInfo as si

def no_emit(msg_header, s): return


def emit_to_print(msg_header, s):
    print(msg_header)
    print(s)

def emit_to_list(header, msg):
    response.append([header, msg])

def build_reader(input_dir, params):
    # build reader

    # get file info
    otsim = OceanTrackerRunMain() # temporary
    file_info, reader_params, reader= otsim._build_sorted_hindcast_files(params['reader'], input_dir)

    # get dummry oceanTrackerSimulation instance with intialised reader
    otsim = OceanTrackerCaseRunner()
    otsim.shared_info.working_params= {'sorted_hindcast_file_info' : file_info}  # nack to give reader acess to hindcastr file info

    params['reader'].update({'time_buffer_size': file_info['n_time_steps_in_hindcast']})  # set buffer size to hindcast size

    reader = otsim._build_class_instance('reader', params['reader'], show_warnings=False)
    reader.initial_setup()

    # fill buffer
    bt = params['shared_params']['backtracking']
    t0 = reader.get_last_time_in_hindcast() if bt else  reader.get_first_time_in_hindcast()

    nb, msg= reader.fill_time_buffer(t0,bt)
    print(msg)
    return reader

class OceanTrackerReRunner(object):
    def __init__(self, pre_built_reader, emit_method):
        self.emit=emit_method
        self.pre_built_reader = pre_built_reader

    def first_run(self, params, test_root_output_dir = None):

        params['shared_params'].update({'processors': 1,  # enforce single core
                                           'input_dir': 'Missing'})

        ot1 = OceanTrackerRunMain()

        if test_root_output_dir is not None:  params['shared_params']['root_output_dir'] = test_root_output_dir

        # add defaults to run params
        params = ot1.merge_and_check_params(params, ot1.run_params_template, find_unknown=False)

        params['base_case_params'] = ot1.merge_and_check_params(params['base_case_params'], ot1.case_params_default_template, find_unknown=False)

        if test_root_output_dir is not None:
            params['shared_params']['root_output_dir']= test_root_output_dir

        ot1. _build_output_dirs(params['shared_params'])
        outputFiles={'output_file_base': 'NoOutputRerunner', 'run_output_dir': 'NoOutpuDir'}
        run_params = ot1._build_run_case_params(params['shared_params'], params['reader'], params['base_case_params'], [], None,outputFiles)


        ot2= OceanTrackerCaseRunner()

        ot2._A2_do_run(run_params[0], pre_built_reader=self.pre_built_reader)

        self.otsim = ot2  # for rerunner


    def rerun(self, case_params, emit_method = emit_to_print):
        # default rerun
        self._do_a_rerun(case_params, emit_method)

    def _do_a_rerun(self, case_params, emit_method):
        # rerun but change only
        # a) by using new release groups
        # b) change custom particle property parameters
        self.emit = emit_method
        otsim = self.otsim
        si = otsim.shared_info
        pgm = otsim.shared_info.core_roles.particle_group_manager
        solver = otsim.shared_info.core_roles.solver
        reader = si.core_roles.reader

        # clear, then add new release groups   re formed with new param
        si.roles.release_groups=[]
        t_start, t_end, estimated_total_particles= otsim._setup_particle_release_groups_and_start_end_times(case_params['release_groups'])

        # adjust shared model run time and duration
        si.model_start_time= t_start
        si.model_duration=  min(abs(t_end - t_start), si.run_params['duration'])

        # reset any stats, reallocate count arrays, based on new release groups
        for s in si.roles.particle_statistics:
            s.initial_setup()

        pgm.info['num_released'] = 0

        solver.solve_for_data_in_buffer()

    def _get_engine_info(self):
        otsim = self.otsim
        grid =  si.core_roles.readergrid

        reader = otsim.shared_info.reader
        t1 = reader.get_first_time_in_hindcast()
        t2 = reader.get_last_time_in_hindcast()
        d = {'max_particles': otsim.shared_info.particle_buffer_size,
             'time_base_seconds_since': reader.params['hindcast_date_of_time_zero'],
             'hindcast': {'start_time': t1,
                          'end_time': t2,
                          'time_start': time_util.seconds_to_isostr(t1),
                          'time_end': time_util.seconds_to_isostr(t2),
                          'nodes': grid['x'].shape[0],
                          },
             }

        return {'model_info' : d, 'grid_outline' : grid['grid_outline'] }

    def emit_engine_info(self):
        d= self._get_engine_info()
        self.emit('engine_info', d)

    def response_start(self):
        self.emit('response_start', {'utcnow': datetime.utcnow().isoformat() + 'Z'})

    def response_end(self):

        # stuff sent and end
        otsim = self.otsim
        self.emit('response_end', {'utcnow': datetime.utcnow().isoformat() + 'Z',
                                   'run_info': {'particles_released' : otsim.shared_info.class_pointers['particle_group_manager'].info['num_released']}
                                   })



if __name__ == '__main__':
    # windows/linux  data source
    pass

    parser = argparse.ArgumentParser()
    parser.add_argument('-cookstrait', action='store_true')
    args = parser.parse_args()

    case = {
            'write_tracks':  False,
            'write_grid': False,
            'solver': {'n_sub_steps': 2},
            'interp2D': {
                'class_name': 'oceantracker.interpolator.interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid'},
            'interp3D': {
                'class_name': 'oceantracker.interpolator.interp_triangle_native_grid.Interp3DTriangular_native_grid'},
            'particle_group_manager': {'class_name': 'OTreRunner.EmitOutputParticle'},
            'dispersion': {'A_H': 0.1, },
            'release_groups': [
                {'points': [[1594500, 5482700], [1598000, 5486100]],
                 'pulse_size': 1, 'release_interval': 6 * 3600},
                {'class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
                 'points': [[1597682.1237, 5489972.7479],
                            [1598604.1667, 5490275.5488],
                            [1598886.4247, 5489464.0424],
                            [1597917.3387, 5489000],
                            [1597300, 5489000]],
                 'pulse_size': 1, 'release_interval': 6 * 3600}
            ],

            # add custom property adds to otsim for build
            'particle_properties': [
                {'class_name': 'oceantracker.particle_properties.distance_travelled.distance_travelled'}],
            'particle_statistics': []
            }

    if args.cookstrait:
        input_dir = 'F:\HindcastReWrites\oceantrackerFMT\OceanPlasticsSim2021'
        reader_dict = {'class_name': 'oceantracker.reader.generic_ncdf_readerUnstructured.GenericReaderNCDF',
                       'file_mask': 'CookStraitSounds05.nc',
                       'isodate_of_hindcast_time_zero': '1970-01-01',
                       'water_velocity_map': {'u': 'u', 'v': 'v'},
                       'field_map': {},
                       'dimension_map': {'space': 'node', 'time': 'time'},
                       'grid_map': {'time': 'time',
                                    'x': 'x', 'y': 'y',
                                   },
                       'time_buffer_size': 48}

    else:
        input_dir = '../../demos/demo_hindcast'
        reader_dict = {'class_name': 'oceantracker.reader.generic_ncdf_readerUnstructured.GenericReaderNCDF',
                       'file_mask': 'demoHindcast2D*.nc',
                       'isodate_of_hindcast_time_zero': '2017-01-01',
                       'water_velocity_map': {'u': 'east_vel', 'v': 'north_vel'},
                       'field_map': {},
                       'dimension_map': {'space': 'node', 'time': 'time'},
                       'grid_map': {'time': 'time_sec',
                                    'x': 'east', 'y': 'north',
                                    'triangles': 'tri',
                                   },
                       'time_buffer_size': 48}

    s = __file__.split('oceantracker02')
    params = dict(processors=1, root_output_dir=s[0]+'/oceantracker02/demos/output/reRunner', input_dir=input_dir,
                  output_file_base='rerun_test',
                  reader=reader_dict,
                  case_list=[case])

    # 1) prebuild reader
    reader = build_reader(input_dir,params)

    # 2) set up an rerunnable engine using first run
    ot_rerunner = OceanTrackerReRunner(reader)
    ot_rerunner.first_run(params)

    # 3) now test rerunner for a point and an polygon
    prg = [
        {'release_start_date': '2017-01-05', 'points': [[1594500, 5482700], [
            1598000, 5486100]], 'pulse_size': 10, 'release_interval': 1 * 3600},
        {'release_start_date': '2017-01-05',
            'class_name': 'oceantracker.release_groups.polygon_release.PolygonRelease',
         'points': [[1597682.1237, 5489972.7479],
                    [1598604.1667, 5490275.5488],
                    [1598886.4247, 5489464.0424],
                    [1597917.3387, 5489000],
                    [1597300, 5489000]],
         'pulse_size': 10, 'release_interval': 3 * 3600}

    ]
    # loop over misc
    print('rerunner misc')
    for pg in prg:
        print(pg)
        ot_rerunner.rerun(pg)


    # 4) now create custom emit and rerun.

    response = []



    for pg in prg:
        print(pg)
        response = []
        ot_rerunner.rerun(pg, emit_method=emit_to_list)
        print(len(response))
        print(len(response[-3][1]['crds']))

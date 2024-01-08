def get_run_params():
    a=1

def reponse_end(self):

    # stuff sent and end

    # send individual particle stats
    particle = self.otsim.shared_info.classes['particle_group_manager']
    s = particle.get_partProp_inBufferPtr('distance_travelled').copy()
    time_alive = particle.get_partProp_inBufferPtr('age').copy()
    time_alive[time_alive == 0] = 1e32

    speed = s / time_alive
    time_alive[np.isnan(time_alive)] = -999.0
    s[np.isnan(s)] = -999.0
    speed[np.isnan(speed)] = -999.0

    self.emit('particle_stats', {
        'time_alive': time_alive.tolist(),
        'distance_travelled_meters': s.tolist(),
        'average_speed_ms': speed.tolist(),
    })

    self.emit('response_end', {
        'utcnow': datetime.utcnow().isoformat() + 'Z'})


class EmitOutputParticle(ParticleGroup):
    def __init__(self):
        super().__init__()
        self.emit = no_emit

    def set_emit(self, f):
        self.emit = f

    def write_step(self):
        # writes each time step
        # Cast to int32 to save space
        si=self.shared_info
        particle_locations = np.asarray(self.get_partProp_inBufferPtr('x'), dtype = np.int32)
        status = np.array(self.get_partProp_inBufferPtr('status'), dtype = np.int8)  # Cast to int8

        self.emit('response', {
            'realtime': int(si.classes['time_varying_info']['time'].get()),
            'num_released': self.info['num_released'],
            'crds':  particle_locations,
            'status':  status,
        })

if __name__ == '__main__':

    if 1==0:

        case = {
                'write_tracks':  False,
                'write_grid': False,
                'particle_buffer_size': 500,
                'solver': {'n_sub_steps': 2},
                'interp2D': {'class_name': 'oceantracker.interpolator.interp_triangle_native_grid.InterpTriangularNativeGrid_Slayer_and_LSCgrid'},
                'interp3D': {'class_name': 'oceantracker.interpolator.interp_triangle_native_grid.Interp3DTriangular_native_grid'},
                'particle_group_manager': {'class_name': 'OTreRunner.EmitOutputParticle'},
                'dispersion': {'A_H': .1, },
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
                    {'class_name': 'oceantracker.particle_properties.distance_travelled.DistanceTravelled'}],
                'particle_statistics': []
                }

    else:
        input_dir = '../../../../demos/demo_hindcast'
        reader_dict = {'class_name': 'oceantracker.reader.generic_ncdf_readerUnstructured.GenericReaderNCDF',
                       'file_mask': 'demoHindcast2D*.nc',
                       'isodate_of_hindcast_time_zero': '2017-01-01',
                       'water_velocity_map': {'u': 'east_vel', 'v': 'north_vel'},
                       'field_map': {},
                       'dimension_map': {'space': 'node', 'time': 'time'},
                       'grid_map': {'time': 'time_sec',
                                    'x': 'east', 'y': 'north',
                                    'triangles': 'tri',
                                    'dry_cells': 'dry_cell_flag'},
                       'time_buffer_size': 48}

    s = __file__.split('oceantracker02')
    params = dict(processors=1, root_output_dir=s[0]+'/oceantracker02/demos/output/reRunner', input_dir=input_dir,
                  output_file_base='rerun_test',
                  reader=reader_dict,
                  case_list=[case])

    # 1) prebuild reader
    ot0 = OceanTrackerReRunner()
    reader = ot0.setup_reader_fields(params)

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

    def emit_to_list(header, msg):
        response.append([header, msg])

    for pg in prg:
        print(pg)
        response = []
        ot_rerunner.rerun(pg, emit_method=emit_to_list)
        print(len(response))
        print(len(response[-3][1]['crds']))

from os import path,chdir, mkdir

from oceantracker.main import OceanTracker

if __name__ == "__main__":
    # nested NZ schisim with a  glorys subset
    ot = OceanTracker()
    ot.settings(output_file_base = 'sea_spurge_test01',
                root_output_dir= r'D:\OceanTrackerOutput',
                time_step=1800,
                max_run_duration = 10*24*3600., # 10 days
                #display_grid_at_start=True
                )
    # Glorys outer grid
    ot.add_class('reader',
                 input_dir=r'D:\Hindcast_reader_tests\Glorys\glorysRemySeaSpurgeSurfaceTestData2D',
                 file_mask = '*.nc')  # mask covering hindcast and static variables

    #NZ surface hindcast
    ot.add_class('nested_readers',
                input_dir=r'D:\Hindcast_reader_tests\Schisim\NZsurface2D_seaspurge',
                file_mask = 'schism_*.nc',
                grid_variable_map= dict(x='longitude', y= 'latitude'), # remap x to long lat
                field_variable_map=dict(water_velocity=['vsurf']),  # remap velocity
                # hgrid needed for open boundary info
                hgrid_file_name= path.join(r'D:\Hindcast_reader_tests\Schisim\NZsurface2D_seaspurge','hgridNZ_run.gr3')
                )
    x0 =  [ [174.665532083399,-35.922300421719214],
            [167.70585302583135, -41.09760403942677],
            [168.18486957886807, -41.126477553835635],
            [178.78311081480544, -34.83205141270341],
            [179.74114392087887, -35.81375090260477],
            [ 178.9627420221942, -41.47295972674199]
           ]
    ot.add_class('release_groups',
                 points = x0,
                 pulse_size=10,
                 release_interval=1800)

    # note all param can be seen at ot.params

    # do run
    case_info_file= ot.run()


    if case_info_file is not None:
        from plot_oceantracker import plot_tracks
        from read_oceantracker.python import load_output_files
        tracks =load_output_files.load_track_data(case_info_file,
                                        gridID=1) # plot inner gridID=1, not outer gridID = 0
        anim = plot_tracks.animate_particles(tracks,colour_using_data=tracks['hydro_model_gridID'],
                                             back_ground_depth=False, vmin=0,vmax=1,
                                             show_grid=True, show_dry_cells=True, axis_labels=True,
                                             )




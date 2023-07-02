Minimal example
===============

[This note-book is in oceantracker/tutorials_how_to/]

Main steps are

1. build parameters, ie. provide users settings and add “classes” with
   their specific settings, to the computational pipeline.

2. run oceantracker with these parameters

3. plot results

See next notebook for more details on the process.

This example uses helper methods of OceanTracker class to build
parameters. The example is part of a a 3D Schisim model, where particles
always re-suspend if the land on the bottom. Particles stranded by the
falling tide in dry cells are frozen, until the cell becomes wet.

.. code:: ipython3

    # minimal_example.py using class helper method
    #------------------------------------------------
    from oceantracker.main import OceanTracker
    
    # make instance of oceantracker to use to set parameters using code, then run
    ot = OceanTracker()
    
    # ot.settings method use to set basic settings
    ot.settings(output_file_base='minimal_example', # name used as base for output files
                root_output_dir='output',             #  output is put in dir   'root_output_dir'\\'output_file_base'
                time_step= 120. #  2 min time step as seconds
                )
    # ot.set_class, sets parameters for a named class
    ot.add_class('reader',input_dir= '../demos/demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                          file_mask=  'demoHindcastSchism*.nc')  # hindcast file mask
    # add  release locations from two points,
    #               (ie locations where particles are released at the same times and locations)
    # note : can add multiple release groups
    ot.add_class('release_groups', name='my_release_point', # user must provide a name for group first
                        points= [[1595000, 5482600],        #[x,y] pairs of release locations
                                 [1599000, 5486200]],      # must be an N by 2 or 3 or list, convertible to a numpy array
                        release_interval= 3600,           # seconds between releasing particles
                        pulse_size= 10,                   # number of particles released each release_interval
                )
    # run oceantracker
    case_info_file_name = ot.run()
    
    # output now in folder output/minimal_example
    # case_info_file_name the name a json file with useful info for post processing, eg output file names
    print(case_info_file_name)
    


.. parsed-literal::

    helper: --------------------------------------------------------------------------
    helper: Starting OceanTracker helper class
    helper:   - Starting run using helper class
    main: --------------------------------------------------------------------------
    main: OceanTracker- preliminary setup
    main:      Python version: 3.10.9 | packaged by conda-forge | (main, Jan 11 2023, 15:15:40) [MSC v.1916 64 bit (AMD64)]
    main:   - found hydro-model files of type SCHISIM
    main:       -  sorted hyrdo-model files in time order,	  0.099 sec
    main:     >>> Note: output is in dir= e:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\minimal_example
    main:     >>> Note: to help with debugging, parameters as given by user  are in "minimal_example_raw_user_params.json"
    C000: --------------------------------------------------------------------------
    C000: Starting case number   0,  minimal_example at 2023-06-27T13:57:21.699403
    C000: --------------------------------------------------------------------------
    C000:       -  built node to triangles map,	  0.820 sec
    C000:       -  built triangle adjacency matrix,	  0.273 sec
    C000:       -  found boundary triangles,	  0.000 sec
    C000:       -  built domain and island outlines,	  1.561 sec
    C000:       -  calculated triangle areas,	  0.000 sec
    C000:   Finished grid setup
    C000:       -  set up release_groups,	  0.002 sec
    C000:       -  built barycentric-transform matrix,	  0.452 sec
    C000:       -  initial set up of core classes,	  0.469 sec
    C000:       -  final set up of core classes,	  0.001 sec
    C000:       -  created particle properties derived from fields,	  0.003 sec
    C000: >>> Note: No open boundaries requested, as run_params["open_boundary_type"] = 0
    C000:       Hint: Requires list of open boundary nodes not in hydro model, eg for Schism this can be read from hgrid file to named in reader params and run_params["open_boundary_type"] = 1
    C000: --------------------------------------------------------------------------
    C000:   - Starting minimal_example,  duration: 0 days 23 hrs 0 min 0 sec
    C000:       -  Initialized Solver Class,	  0.000 sec
    C000: 00% step 0000:H0000b00-01 Day +00 00:00 2017-01-01 00:30:00: Rel.:      20: Active:00020 M:00020 S:00000  B:00000 D:000 O:00 N:000 Buffer:0020 -  0% step time = 6197.3 ms
    C000:   - Reading-file-00  demoHindcastSchism3D.nc, steps in file  24, steps  available 000:023, reading  24 of 48 steps,  for hydo-model time steps 00:23,  from file offsets 00:23,  into ring buffer offsets 000:023 
    C000:       -  read  24 time steps in  0.6 sec
    C000:   - opening tracks output to : minimal_example_tracks_compact.nc
    C000: 04% step 0030:H0001b01-02 Day +00 01:00 2017-01-01 01:30:00: Rel.:      40: Active:00040 M:00036 S:00000  B:00004 D:000 O:00 N:000 Buffer:0040 -  0% step time = 2977.9 ms
    C000: 09% step 0060:H0002b02-03 Day +00 02:00 2017-01-01 02:30:00: Rel.:      60: Active:00060 M:00053 S:00000  B:00007 D:000 O:00 N:000 Buffer:0060 -  0% step time = 61.1 ms
    C000: 13% step 0090:H0003b03-04 Day +00 03:00 2017-01-01 03:30:00: Rel.:      80: Active:00080 M:00066 S:00011  B:00003 D:000 O:00 N:000 Buffer:0080 -  0% step time = 59.9 ms
    C000: 17% step 0120:H0004b04-05 Day +00 04:00 2017-01-01 04:30:00: Rel.:     100: Active:00100 M:00081 S:00012  B:00007 D:000 O:00 N:000 Buffer:0100 -  0% step time = 60.1 ms
    C000: 22% step 0150:H0005b05-06 Day +00 05:00 2017-01-01 05:30:00: Rel.:     120: Active:00120 M:00104 S:00012  B:00004 D:000 O:00 N:000 Buffer:0120 -  0% step time = 62.1 ms
    C000: 26% step 0180:H0006b06-07 Day +00 06:00 2017-01-01 06:30:00: Rel.:     140: Active:00140 M:00124 S:00012  B:00004 D:000 O:00 N:000 Buffer:0140 -  0% step time = 61.9 ms
    C000: 30% step 0210:H0007b07-08 Day +00 07:00 2017-01-01 07:30:00: Rel.:     160: Active:00160 M:00142 S:00012  B:00006 D:000 O:00 N:000 Buffer:0160 -  0% step time = 62.6 ms
    C000: 35% step 0240:H0008b08-09 Day +00 08:00 2017-01-01 08:30:00: Rel.:     180: Active:00180 M:00165 S:00011  B:00004 D:000 O:00 N:000 Buffer:0180 -  0% step time = 63.0 ms
    C000: 39% step 0270:H0009b09-10 Day +00 09:00 2017-01-01 09:30:00: Rel.:     200: Active:00200 M:00192 S:00000  B:00008 D:000 O:00 N:000 Buffer:0200 -  0% step time = 64.0 ms
    C000: 43% step 0300:H0010b10-11 Day +00 10:00 2017-01-01 10:30:00: Rel.:     220: Active:00220 M:00203 S:00000  B:00017 D:000 O:00 N:000 Buffer:0220 -  0% step time = 64.1 ms
    C000: 48% step 0330:H0011b11-12 Day +00 11:00 2017-01-01 11:30:00: Rel.:     240: Active:00240 M:00223 S:00000  B:00017 D:000 O:00 N:000 Buffer:0240 -  0% step time = 64.4 ms
    C000: 52% step 0360:H0012b12-13 Day +00 12:00 2017-01-01 12:30:00: Rel.:     260: Active:00260 M:00240 S:00000  B:00020 D:000 O:00 N:000 Buffer:0260 -  0% step time = 64.8 ms
    C000: 57% step 0390:H0012b12-13 Day +00 13:00 2017-01-01 13:30:00: Rel.:     280: Active:00280 M:00256 S:00011  B:00013 D:000 O:00 N:000 Buffer:0280 -  0% step time = 66.8 ms
    C000: 61% step 0420:H0014b14-15 Day +00 14:00 2017-01-01 14:30:00: Rel.:     300: Active:00300 M:00271 S:00018  B:00011 D:000 O:00 N:000 Buffer:0300 -  0% step time = 66.3 ms
    C000: 65% step 0450:H0015b15-16 Day +00 15:00 2017-01-01 15:30:00: Rel.:     320: Active:00320 M:00256 S:00054  B:00010 D:000 O:00 N:000 Buffer:0320 -  0% step time = 66.2 ms
    C000: 70% step 0480:H0016b16-17 Day +00 16:00 2017-01-01 16:30:00: Rel.:     340: Active:00340 M:00273 S:00062  B:00005 D:000 O:00 N:000 Buffer:0340 -  0% step time = 66.3 ms
    C000: 74% step 0510:H0017b17-18 Day +00 17:00 2017-01-01 17:30:00: Rel.:     360: Active:00360 M:00285 S:00071  B:00004 D:000 O:00 N:000 Buffer:0360 -  0% step time = 68.3 ms
    C000: 78% step 0540:H0018b18-19 Day +00 18:00 2017-01-01 18:30:00: Rel.:     380: Active:00380 M:00307 S:00071  B:00002 D:000 O:00 N:000 Buffer:0380 -  0% step time = 67.5 ms
    C000: 83% step 0570:H0019b19-20 Day +00 19:00 2017-01-01 19:30:00: Rel.:     400: Active:00400 M:00325 S:00069  B:00006 D:000 O:00 N:000 Buffer:0400 -  0% step time = 68.1 ms
    C000: 87% step 0600:H0020b20-21 Day +00 20:00 2017-01-01 20:30:00: Rel.:     420: Active:00420 M:00344 S:00061  B:00015 D:000 O:00 N:000 Buffer:0420 -  0% step time = 69.3 ms
    C000: 91% step 0630:H0021b21-22 Day +00 21:00 2017-01-01 21:30:00: Rel.:     440: Active:00440 M:00403 S:00018  B:00019 D:000 O:00 N:000 Buffer:0440 -  0% step time = 70.6 ms
    C000: 96% step 0660:H0022b22-23 Day +00 22:00 2017-01-01 22:30:00: Rel.:     460: Active:00460 M:00420 S:00011  B:00029 D:000 O:00 N:000 Buffer:0460 -  0% step time = 71.4 ms
    C000: 100% step 0689:H0022b22-23 Day +00 22:58 2017-01-01 23:28:00: Rel.:     460: Active:00460 M:00433 S:00000  B:00027 D:000 O:00 N:000 Buffer:0460 -  0% step time = 71.6 ms
    C000: >>> Note: No open boundaries requested, as run_params["open_boundary_type"] = 0
    C000:       Hint: Requires list of open boundary nodes not in hydro model, eg for Schism this can be read from hgrid file to named in reader params and run_params["open_boundary_type"] = 1
    C000:   -  Triangle walk summary: Of  752,024 particles located  0, walks were too long and were retried,  of these  0 failed after retrying and were discarded
    C000: --------------------------------------------------------------------------
    C000:   - Finished case number   0,  minimal_example started: 2023-06-27 13:57:21.698403, ended: 2023-06-27 13:57:36.909100
    C000:       Elapsed time =0:00:15.210697
    C000: --------------------------------------------------------------------------
    main:     >>> Note: run summary with case file names   "minimal_example_runInfo.json"
    main:     >>> Note: output is in dir= e:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\minimal_example
    main:     >>> Note: to help with debugging, parameters as given by user  are in "minimal_example_raw_user_params.json"
    main:     >>> Note: run summary with case file names   "minimal_example_runInfo.json"
    main: --------------------------------------------------------------------------
    main: OceanTracker summary:  elapsed time =0:00:15.373736
    main:       Cases -   0 errors,   0 warnings,   2 notes, check above
    main:       Helper-   0 errors,   0 warnings,   0 notes, check above
    main:       Main  -   0 errors,   0 warnings,   3 notes, check above
    main: --------------------------------------------------------------------------
    e:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\minimal_example\minimal_example_caseInfo.json
    

Read and plot output
--------------------

A first basic plot of particle tracks

.. code:: ipython3

    # read output files
    from oceantracker.post_processing.read_output_files import  load_output_files
    
    # read particle track data into a dictionary using case_info_file_name
    tracks = load_output_files.load_track_data(case_info_file_name)
    print(tracks.keys()) # show what is in tracks dictionary holds
    
    from oceantracker.post_processing.plotting.plot_tracks import plot_tracks
    
    ax= [1591000, 1601500, 5478500, 5491000]  # area to plot
    plot_tracks(tracks, axis_lims=ax)


.. parsed-literal::

    dict_keys(['file_created', 'total_num_particles_released', 'time_steps_written', 'status_unknown', 'status_bad_cord', 'status_cell_search_failed', 'status_notReleased', 'status_dead', 'status_outside_open_boundary', 'status_frozen', 'status_stranded_by_tide', 'status_on_bottom', 'status_moving', 'release_groupID_my_release_point', 'dimensions', 'status', 'tide', 'release_points', 'IDpulse', 'IDrelease_group', 'age', 'x0', 'is_polygon_release', 'number_of_release_points', 'friction_velocity', 'particles_written_per_time_step', 'user_release_groupID', 'x_last_good', 'time_step_range', 'x', 'time_released', 'ID', 'particle_ID', 'water_depth', 'dry_cell_index', 'num_part_released_so_far', 'time', 'release_groupID', 'release_locations', 'z', 'grid', 'particle_status_flags', 'particle_release_groups', 'full_case_params', 'axis_lim'])
    


.. image:: A_minimal_example_files%5CA_minimal_example_3_1.png


Add aminations
--------------

play movie when done

animations require additional install of ffpeg, after activating
oceantracker conda environment run

``conda install -c conda-forge ffmpeg``

In animation, sand colored area shows dry cells, blue particles are
moving, green are stranded by the tide in dry cells, gray are on the sea
bed, from which they resupend in this example.

By default particles are blocked from moving from a wet cell to a dry
cell and will not be released if the release location lies within a dry
cell.

.. code:: ipython3

    from matplotlib import pyplot as plt
    from oceantracker.post_processing.plotting.plot_tracks import animate_particles
    from IPython.display import HTML
    
    # animate particles
    anim = animate_particles(tracks, axis_lims=ax,title='Minimal OceanTracker example', 
                             show_dry_cells=True, show_grid=True, show=False) # use ipython to show video, rather than matplotlib plt.show()
    
    # this is slow to build! 
    HTML(anim.to_html5_video())

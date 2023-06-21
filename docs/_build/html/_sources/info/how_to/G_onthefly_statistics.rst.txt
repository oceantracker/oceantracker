On-the-fly statistics
=====================

[This note-book is in oceantracker/tutorials_how_to/]

Scaling up particle numbers to millions will create large volumes of
particle track data. Storing and analyzing these tracks is slow and
rapidly becomes overwhelming. For example, building a heat map from a
terabyte of particle tracks after a run has completed. Ocean tracker can
build some particle statistics on the fly, without recording any
particle tracks. This results in more manageable data volumes and
analysis.

On-the-fly statistics record particle counts separately for each release
group. It is also possible to subset the counts, ie only count particles
which are stranded by the tide by designating a range of particle status
values to count. Or, only count particles in a given vertical “z” range.
Users can add multiple statistics, all calculated in from the same
particles during the run. Eg. could add a particle statistic for each
status type, for different depth ranges.

Statistics can be read, plotted or animated with OceanTrackers
post-processing code, see below

The available “particle_statistics” classes with their individual
settings are at …. add link

Currently there are two main classes of 2D particle statistics “gridded”
which counts particles inside cells of a regular grid, and “polygon”
which counts particles in a given list of polygons.

The user can add many particle statistics classes, all based on the same
particles. For both types it is possible to only count a subset of these
particles, by setting a min. and/or max status to count, or setting a
min. and/or max. “z”, the vertical location. So could add several
statistics classes, each counting particles in different layers, or
classes to separately count those moving and those on the bottom hoping
to be re-suspended.

Gridded statistics
------------------

These are heat maps of counts binned into cells of a regular grid. Along
with heat maps of particle counts, users can optionally build a heat
maps of named particle properties, eg. the value decaying particle
property. To ensure the heat map grids are not too large or too coarse,
by default grids are centred on each release group, thus there are
different grid locations for each release group.

Polygon statistics
------------------

These particle counts can be used to calculate the connectivity between
each release group and a user given list of “statistics” polygons. Also,
used to estimate the influence of each release group on a particle
property with each given statistics polygon. The statistics polygons are
not the same as those used in a polygon release (they can be if the user
requires it). Polygon statistics show effect of each point or polygon
release, on the given statistics polygons. A special case of a polygon
statistic, is the “residence_time” class, which can be used to calculate
the fraction of particles from each release group remaining within each
statistics polygon at each ‘update_interval’ as one way to estimate
particle residence time for each release group.

Particle property statistics
----------------------------

Both types of statistics can also record sums of user designated
particle properties within each given grid cell or statistics polygon,
which originate from each release group. These sums enabling mean values
of designated particle properties within each grid cell or polygon to be
calculated. They can also be used to estimate the relative influence of
each release group on the value of a particle property within each given
grid cell or polygon.

A future version with allow estimating the variance of the designated
property values and particle counts in each grid cell or polygon, for
each release group.

Gridded/Heat map example
------------------------

The below uses the helper class method to extends the minimal_example to
add

-  Decaying particle property, eg. breakdown of a pollutant
-  Gridded time series of particle statistics as heat maps, which also
   builds a heat map of the pollutant
-  Plot the particle counts and pollutant as animated heatmap.

.. code:: ipython3

    # Gridded Statistics example.py using class helper method
    #------------------------------------------------
    from oceantracker.main import OceanTracker
    
    # make instance of oceantracker to use to set parameters using code, then run
    ot = OceanTracker()
    
    # ot.settings method use to set basic settings
    ot.settings(output_file_base='heat_map_example', # name used as base for output files
                root_output_dir='output',             #  output is put in dir   'root_output_dir'\\'output_file_base'
                time_step= 600., #  10 min time step as seconds
                write_tracks = False # particle tracks not needed for on fly 
                )
    # ot.set_class, sets parameters for a named class
    ot.add_class('reader',input_dir= '../demos/demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                          file_mask=  'demoHindcastSchism*.nc')  # hindcast file mask
    
    # add one release locations 
    ot.add_class('release_groups', name='my_release_point', # user must provide a name for group first
                            points= [ [1599000, 5486200]],       # ust be 1 by N list pairs of release locations
                            release_interval= 900,           # seconds between releasing particles
                            pulse_size= 1000,                   # number of particles released each release_interval
                )
    # add a decaying particle property
    # add and Age decay particle property, with exponential decay based on age, with time scale 1 hour                             
    ot.add_class('particle_properties', # add a new property to particle_properties role
                name ='a_pollutant', # must have a user given name
                class_name='oceantracker.particle_properties.age_decay.AgeDecay', #  class_role is resuspension
                initial_value= 1000,
                decay_time_scale = 3600.) # time scale of age decay ie decays initial_value* exp(-age/decay_time_scale)
    
    # add a gridded particle statistic 
    ot.add_class('particle_statistics', 
                    name = 'my_heatmap',
                    class_name= 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
                    # the below settings are optional
                    update_interval = 900, # time interval in sec, between doing particle statists counts 
                    particle_property_list = ['a_pollutant'], # request a heat map for the decaying part. prop. added above
                    status_min ='moving', # only count the particles which are moving 
                    z_mi =-2.,  # only count particles at locations above z=-2m
                    grid_size= [120, 121]  # number of east and north cells in the heat map
                    )
    
    
    # run oceantracker
    case_info_file_name = ot.run()


::


    ---------------------------------------------------------------------------

    AttributeError                            Traceback (most recent call last)

    Cell In[1], line 46
         33 ot.add_class('particle_statistics', 
         34                 name = 'my_heatmap',
         35                 class_name= 'oceantracker.particle_statistics.gridded_statistics.GriddedStats2D_timeBased',
       (...)
         41                 grid_size= [120, 121]  # number of east and north cells in the heat map
         42                 )
         45 # run oceantracker
    ---> 46 case_info_file_name = ot.run()
    

    AttributeError: 'OceanTracker' object has no attribute 'run'


Read and plot heat maps
~~~~~~~~~~~~~~~~~~~~~~~

The statistics output from the above run is in file
output:raw-latex:`\heat`\_map_example:raw-latex:`\heat`\_map_example_stats_gridded_time_my_heatmap.nc

This netcdf file can be read and organized as a python dictionary by
directly with read_ncdf_output_files.read_stats_file.

To plot use, load_output_files.load_stats_data, which also loads grid
etc for plotting

.. code:: ipython3

    # read stats files
    from oceantracker.post_processing.read_output_files import read_ncdf_output_files, load_output_files
    from oceantracker.post_processing.plotting import plot_statistics
    from IPython.display import HTML
    
    # basic read of net cdf
    raw_stats = read_ncdf_output_files.read_stats_file('output/heat_map_example/heat_map_example_stats_gridded_time_my_heatmap.nc')
    print('raw_stats', raw_stats.keys())
    
    # better,  load netcdf plus grid and other data useful in plotting 
    # uses case_info name returned from run above
    stats_data = load_output_files.load_stats_data(case_info_file_name,'my_heatmap')
    print('stats',stats_data.keys())
    
    # use stats_data variable to plot heat map at last time step, by default plots var= "count"
    ax= [1591000, 1601500, 5478500, 5491000] 
    anim= plot_statistics.animate_heat_map(stats_data, release_group='my_release_point', axis_lims=ax,
                        heading='Particle count heatmap built on the fly, no tracks recorded', fps=1)
    HTML(anim.to_html5_video())# this is slow to build!
    
    # animate the pollutant
    anim= plot_statistics.animate_heat_map(stats_data, var='a_pollutant',release_group= 'my_release_point', axis_lims=ax,
                        heading='Decaying particle property , a_pollutant built on the fly, no tracks recorded', fps=1)
    HTML(anim.to_html5_video())# this is slow to build!
    
    
    # static heat map
    plot_statistics.plot_heat_map(stats_data, var='a_pollutant',release_group= 'my_release_point', axis_lims=ax,  heading='a_pollutant at last time step  depth built on the fly, no tracks recorded')


.. parsed-literal::

    raw_stats dict_keys(['total_num_particles_released', 'release_groupID_my_release_point', 'dimensions', 'limits', 'release_groupID', 'release_locations', 'grid_cell_area', 'count_all_particles', 'num_released', 'y', 'sum_a_pollutant', 'release_points', 'number_of_release_points', 'count', 'x', 'is_polygon_release', 'number_released_each_release_group', 'time', 'time_var', 'date', 'stats_type', 'connectivity_matrix', 'a_pollutant'])
    stats dict_keys(['total_num_particles_released', 'release_groupID_my_release_point', 'dimensions', 'limits', 'release_groupID', 'release_locations', 'grid_cell_area', 'count_all_particles', 'num_released', 'y', 'sum_a_pollutant', 'release_points', 'number_of_release_points', 'count', 'x', 'is_polygon_release', 'number_released_each_release_group', 'time', 'time_var', 'date', 'stats_type', 'connectivity_matrix', 'a_pollutant', 'info', 'params', 'release_group_centered_grids', 'particle_status_flags', 'particle_release_groups', 'full_case_params', 'grid'])
    animate_heat_map> colour axis limits [0, 4023] [0, 4023]
    


.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_4_1.png


.. parsed-literal::

    animate_heat_map> colour axis limits [1.4321606718741004e-07, 1000.0] [1.4321606718741004e-07, 1000.0]
    


.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_4_3.png



.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_4_4.png


Polygon example
---------------

::

   # add polygon stats example with plotting

.. code:: ipython3

    # Polygon Statistics example.py run using dictionary of parameters
    #------------------------------------------------
    from oceantracker import main
    
    params = main.param_template()  # start with template
    params['output_file_base']='polygon_connectivity_map_example'  # name used as base for output files
    params['root_output_dir']='output'             #  output is put in dir   'root_output_dir'\\'output_file_base'
    params['time_step']= 600. #  10 min time step as seconds
    params['write_tracks'] = False # particle tracks not needed for on fly 
    
    # ot.set_class, sets parameters for a named class
    params['reader']= { 'input_dir': '../demos/demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                        'file_mask':  'demoHindcastSchism*.nc'}  # hindcast file mask
    
    # add one release locations 
    params['release_groups']['my_release_point']={ # user must provide a name for group first
                            'points': [ [1599000, 5486200]],       # ust be 1 by N list pairs of release locations
                            'release_interval': 900,           # seconds between releasing particles
                            'pulse_size': 1000,                   # number of particles released each release_interval
                }
    
    # add a gridded particle statistic 
    params['particle_statistics']['my_polygon']= {
                    'class_name': 'oceantracker.particle_statistics.polygon_statistics.PolygonStats2D_timeBased',
                    'polygon_list': [{'points': [   [1597682.1237, 5489972.7479],# list of one or more polygons
                                                    [1598604.1667, 5490275.5488],
                                                    [1598886.4247, 5489464.0424],
                                                    [1597917.3387, 5489000],
                                                    [1597300, 5489000], [1597682.1237, 5489972.7479]
                                                    ]                                         
                                      }],
                    # the below settings are optional
                    'update_interval': 900, # time interval in sec, between doing particle statists counts 
                    'status_min':'moving', # only count the particles which are moving 
                    }
    
    # run oceantracker
    poly_case_info_file_name = main.run(params)


.. parsed-literal::

    main: --------------------------------------------------------------------------
    main: OceanTracker- preliminary setup
    main:      Python version: 3.10.9 | packaged by conda-forge | (main, Jan 11 2023, 15:15:40) [MSC v.1916 64 bit (AMD64)]
    main:   - found hydro-model files of type SCHISIM
    main:       -  sorted hyrdo-model files in time order,	  0.007 sec
    main:     >>> Note: output is in dir= e:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\polygon_connectivity_map_example
    main:     >>> Note: to help with debugging, parameters as given by user  are in "polygon_connectivity_map_example_raw_user_params.json"
    C000: --------------------------------------------------------------------------
    C000: Starting case number   0,  polygon_connectivity_map_example at 2023-06-21T17:05:37.609665
    C000: --------------------------------------------------------------------------
    C000:       -  built node to triangles map,	  0.000 sec
    C000:       -  built triangle adjacency matrix,	  0.000 sec
    C000:       -  found boundary triangles,	  0.000 sec
    C000:       -  built domain and island outlines,	  0.632 sec
    C000:       -  calculated triangle areas,	  0.000 sec
    C000:   Finished grid setup
    C000:       -  set up release_groups,	  0.000 sec
    C000:       -  built barycentric-transform matrix,	  0.000 sec
    C000:       -  initial set up of core classes,	  0.016 sec
    C000:       -  final set up of core classes,	  0.001 sec
    C000:       -  created particle properties derived from fields,	  0.003 sec
    C000: >>> Note: No open boundaries requested, as run_params["open_boundary_type"] = 0
    C000:       Hint: Requires list of open boundary nodes not in hydro model, eg for Schism this can be read from hgrid file to named in reader params and run_params["open_boundary_type"] = 1
    C000: --------------------------------------------------------------------------
    C000:   - Starting polygon_connectivity_map_example,  duration: 0 days 23 hrs 0 min 0 sec
    C000:       -  Initialized Solver Class,	  0.000 sec
    C000: 00% step 0000:H0000b00-01 Day +00 00:00 2017-01-01 00:30:00: Rel.:   1,000: Active:01000 M:01000 S:00000  B:00000 D:000 O:00 N:000 Buffer:1000 -  0% step time =  2.2 ms
    C000:   - Reading-file-00  demoHindcastSchism3D.nc, steps in file  24, steps  available 000:023, reading  24 of 48 steps,  for hydo-model time steps 00:23,  from file offsets 00:23,  into ring buffer offsets 000:023 
    C000:       -  read  24 time steps in  0.0 sec
    C000:   - opening tracks output to : polygon_connectivity_map_example_tracks_compact.nc
    C000: 04% step 0006:H0001b01-02 Day +00 01:00 2017-01-01 01:30:00: Rel.:   5,000: Active:05000 M:04769 S:00000  B:00231 D:000 O:00 N:000 Buffer:5000 -  1% step time =  1.5 ms
    C000: 09% step 0012:H0002b02-03 Day +00 02:00 2017-01-01 02:30:00: Rel.:   9,000: Active:09000 M:08527 S:00001  B:00472 D:000 O:00 N:000 Buffer:9000 -  2% step time =  1.5 ms
    C000: 13% step 0018:H0003b03-04 Day +00 03:00 2017-01-01 03:30:00: Rel.:  13,000: Active:13000 M:12234 S:00137  B:00629 D:000 O:00 N:000 Buffer:13000 -  3% step time =  1.7 ms
    C000: 17% step 0024:H0004b04-05 Day +00 04:00 2017-01-01 04:30:00: Rel.:  17,000: Active:17000 M:16185 S:00137  B:00678 D:000 O:00 N:000 Buffer:17000 -  3% step time =  1.6 ms
    C000: 22% step 0030:H0005b05-06 Day +00 05:00 2017-01-01 05:30:00: Rel.:  21,000: Active:21000 M:20106 S:00137  B:00757 D:000 O:00 N:000 Buffer:21000 -  4% step time =  1.6 ms
    C000: 26% step 0036:H0006b06-07 Day +00 06:00 2017-01-01 06:30:00: Rel.:  25,000: Active:25000 M:24027 S:00137  B:00836 D:000 O:00 N:000 Buffer:25000 -  5% step time =  1.6 ms
    C000: 30% step 0042:H0007b07-08 Day +00 07:00 2017-01-01 07:30:00: Rel.:  29,000: Active:29000 M:27698 S:00137  B:01165 D:000 O:00 N:000 Buffer:29000 -  6% step time =  1.7 ms
    C000: 35% step 0048:H0008b08-09 Day +00 08:00 2017-01-01 08:30:00: Rel.:  33,000: Active:33000 M:31466 S:00137  B:01397 D:000 O:00 N:000 Buffer:33000 -  7% step time =  1.7 ms
    C000: 39% step 0054:H0009b09-10 Day +00 09:00 2017-01-01 09:30:00: Rel.:  37,000: Active:37000 M:35538 S:00001  B:01461 D:000 O:00 N:000 Buffer:37000 -  7% step time =  1.8 ms
    C000: 43% step 0060:H0010b10-11 Day +00 10:00 2017-01-01 10:30:00: Rel.:  41,000: Active:41000 M:39256 S:00000  B:01744 D:000 O:00 N:000 Buffer:41000 -  8% step time =  1.8 ms
    C000: 48% step 0066:H0011b11-12 Day +00 11:00 2017-01-01 11:30:00: Rel.:  45,000: Active:45000 M:42987 S:00000  B:02013 D:000 O:00 N:000 Buffer:45000 -  9% step time =  1.8 ms
    C000: 52% step 0072:H0012b12-13 Day +00 12:00 2017-01-01 12:30:00: Rel.:  49,000: Active:49000 M:46934 S:00000  B:02066 D:000 O:00 N:000 Buffer:49000 - 10% step time =  1.8 ms
    C000: 57% step 0078:H0012b12-13 Day +00 13:00 2017-01-01 13:30:00: Rel.:  53,000: Active:53000 M:50865 S:00000  B:02135 D:000 O:00 N:000 Buffer:53000 - 11% step time =  1.8 ms
    C000: 61% step 0084:H0014b14-15 Day +00 14:00 2017-01-01 14:30:00: Rel.:  57,000: Active:57000 M:54566 S:00389  B:02045 D:000 O:00 N:000 Buffer:57000 - 11% step time =  1.8 ms
    C000: 65% step 0090:H0015b15-16 Day +00 15:00 2017-01-01 15:30:00: Rel.:  61,000: Active:61000 M:58430 S:00708  B:01862 D:000 O:00 N:000 Buffer:61000 - 12% step time =  1.8 ms
    C000: 70% step 0096:H0016b16-17 Day +00 16:00 2017-01-01 16:30:00: Rel.:  65,000: Active:65000 M:62521 S:00706  B:01773 D:000 O:00 N:000 Buffer:65000 - 13% step time =  1.8 ms
    C000: 74% step 0102:H0017b17-18 Day +00 17:00 2017-01-01 17:30:00: Rel.:  69,000: Active:69000 M:66368 S:00706  B:01926 D:000 O:00 N:000 Buffer:69000 - 14% step time =  1.8 ms
    C000: 78% step 0108:H0018b18-19 Day +00 18:00 2017-01-01 18:30:00: Rel.:  73,000: Active:73000 M:70090 S:00706  B:02204 D:000 O:00 N:000 Buffer:73000 - 15% step time =  1.8 ms
    C000: 83% step 0114:H0019b19-20 Day +00 19:00 2017-01-01 19:30:00: Rel.:  77,000: Active:77000 M:73799 S:00706  B:02495 D:000 O:00 N:000 Buffer:77000 - 15% step time =  1.9 ms
    C000: 87% step 0120:H0020b20-21 Day +00 20:00 2017-01-01 20:30:00: Rel.:  81,000: Active:81000 M:77447 S:00706  B:02847 D:000 O:00 N:000 Buffer:81000 - 16% step time =  1.9 ms
    C000: 91% step 0126:H0021b21-22 Day +00 21:00 2017-01-01 21:30:00: Rel.:  85,000: Active:85000 M:81374 S:00368  B:03258 D:000 O:00 N:000 Buffer:85000 - 17% step time =  1.9 ms
    C000: 96% step 0132:H0022b22-23 Day +00 22:00 2017-01-01 22:30:00: Rel.:  89,000: Active:89000 M:85175 S:00000  B:03825 D:000 O:00 N:000 Buffer:89000 - 18% step time =  1.9 ms
    C000: 99% step 0137:H0022b22-23 Day +00 22:50 2017-01-01 23:20:00: Rel.:  91,000: Active:91000 M:87051 S:00000  B:03949 D:000 O:00 N:000 Buffer:91000 - 18% step time = 126.2 ms
    C000: >>> Note: No open boundaries requested, as run_params["open_boundary_type"] = 0
    C000:       Hint: Requires list of open boundary nodes not in hydro model, eg for Schism this can be read from hgrid file to named in reader params and run_params["open_boundary_type"] = 1
    C000:   -  Triangle walk summary: Of  31,132,960 particles located  0, walks were too long and were retried,  of these  0 failed after retrying and were discarded
    C000: --------------------------------------------------------------------------
    C000:   - Finished case number   0,  polygon_connectivity_map_example started: 2023-06-21 17:05:37.608665, ended: 2023-06-21 17:05:48.162064
    C000:       Elapsed time =0:00:10.553399
    C000: --------------------------------------------------------------------------
    main:     >>> Note: run summary with case file names   "polygon_connectivity_map_example_runInfo.json"
    main:     >>> Note: output is in dir= e:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\polygon_connectivity_map_example
    main:     >>> Note: to help with debugging, parameters as given by user  are in "polygon_connectivity_map_example_raw_user_params.json"
    main:     >>> Note: run summary with case file names   "polygon_connectivity_map_example_runInfo.json"
    main: --------------------------------------------------------------------------
    main: OceanTracker summary:  elapsed time =0:00:10.665271
    main:       Cases -   0 errors,   0 warnings,   2 notes, check above
    main:       Helper-   0 errors,   0 warnings,   0 notes, check above
    main:       Main  -   0 errors,   0 warnings,   3 notes, check above
    main: --------------------------------------------------------------------------
    

Read polygon/connectivity statistics
------------------------------------

.. code:: ipython3

    #Read polygon stats and calculate connectivity matrix 
    from oceantracker.post_processing.read_output_files import load_output_files
    
    poly_stats_data = load_output_files.load_stats_data(poly_case_info_file_name,'my_polygon')
    print('stats',poly_stats_data.keys())
    
    import matplotlib.pyplot as plt
    plt.plot(poly_stats_data['date'], poly_stats_data['connectivity_matrix'][:,0,0])
    plt.title('Connectivity time series between release point and polygon')
    
    #print(poly_stats_data['date'])


.. parsed-literal::

    stats dict_keys(['total_num_particles_released', 'release_groupID_my_release_point', 'dimensions', 'limits', 'release_groupID', 'release_locations', 'count_all_particles', 'num_released', 'release_points', 'number_of_release_points', 'count', 'is_polygon_release', 'number_released_each_release_group', 'time', 'time_var', 'date', 'stats_type', 'connectivity_matrix', 'info', 'params', 'release_group_centered_grids', 'polygon_list', 'particle_status_flags', 'particle_release_groups', 'full_case_params', 'grid'])
    



.. parsed-literal::

    Text(0.5, 1.0, 'Connectivity time series between release point and polygon')




.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_8_2.png


Time verses Age statistics
--------------------------

Both gridded and polygon statistics come in two types, “time” and “age”.

-  “time” statistics are time series, or snapshots, of particle numbers
   and particle properties at a time interval given by
   “calculation_interval” parameter. Eg. gridded stats showing how the
   heat map of a source’s plume evolves over time.

-  “age” statistics are particle counts and properties binned by
   particle age. The result are age based histograms of counts or
   particle proprieties. This is useful to give numbers in each age band
   arriving at a given grid cell or polygon, from each release group.
   Eg. counting how many larvae are old enough to settle in a polygon or
   grid cell from each potential source location.

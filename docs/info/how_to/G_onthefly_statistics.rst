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
property with each given statistics polygon. Polygon statistics count
the particles from each point or polygon release within each statistics
polygons. The statistics polygons are are completely independent of the
polygons that might be used in any polygon release (they can be the same
if the user gives both the same point coordinates). A special case of a
polygon statistic, is the “residence_time” class, which can be used to
calculate the fraction of particles from each release group remaining
within each statistics polygon at each ‘update_interval’ as one way to
estimate particle residence time for each release group.

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
                    z_min =-2.,  # only count particles at locations above z=-2m
                    grid_size= [120, 121]  # number of east and north cells in the heat map
                    )
    
    
    # run oceantracker
    case_info_file_name = ot.run()


.. parsed-literal::

    helper --------------------------------------------------------------------------
    helper Starting OceanTracker helper class
    helper   - Starting run using helper class
    Main --------------------------------------------------------------------------
    Main OceanTracker starting main:
    Main   - Output dir set up.
    Main >>> Warning: Deleted contents of existing output dir
    Main     >>> Note: to help with debugging, parameters as given by user  are in "heat_map_example_raw_user_params.json"
    Main   Output is in dir "e:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\heat_map_example"
    Main         hint: see for copies of screen output and user supplied parameters, plus all other output
    Main --------------------------------------------------------------------------
    Main  OceanTracker version 0.5.0.000 2024-03-07 - preliminary setup
    Main      Python version: 3.10.10 | packaged by conda-forge | (main, Mar 24 2023, 20:00:38) [MSC v.1934 64 bit (AMD64)]
    Main   - Found input dir "../demos/demo_hindcast"
    Main   - found hydro-model files of type  "SCHISIM"
    Main       -  sorted hyrdo-model files in time order,	  0.916 sec
    C000 --------------------------------------------------------------------------
    C000 Starting case number   0,  heat_map_example at 2024-03-20T14:25:46.534260
    C000 --------------------------------------------------------------------------
    C000       -  Scanned OceanTracker to build short name map to the full class_names,	  0.018 sec
    C000   - Starting grid setup
    C000       -  built node to triangles map,	  0.632 sec
    C000       -  built triangle adjacency matrix,	  0.303 sec
    C000       -  found boundary triangles,	  0.000 sec
    C000       -  built domain and island outlines,	  1.414 sec
    C000       -  calculated triangle areas,	  0.000 sec
    C000   - Finished grid setup
    C000 >>> Note: Hydro-model is "3D"  type "SCHISMreaderNCDF"
    C000       hint: Files found dir and sub-dirs of "../demos/demo_hindcast"
    C000     grid bounding box = [1590046.0 5478274.0] to [1603253.0 5492492.0]
    C000       -  built barycentric-transform matrix,	  0.484 sec
    C000 >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    C000 >>> Note: Found vertical diffusivity profile in hydro-model files
    C000 >>> Note: Using vertical diffusivity profile in hydro-model for vertical random walk
    C000 >>> Warning: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 >>> Warning: Making scheduler: update interval rounded to be integer number of time steps
    C000       hint: 900 sec. rounded to model time step = 1200 sec.
    C000       in:  adding scheduler
    C000       -  Set up run start and end times, plus release groups and their schedulers,	  0.000 sec
    C000       -  final set up of core classes,	  0.002 sec
    C000 --------------------------------------------------------------------------
    C000   - Starting heat_map_example,  duration: 0 days 22 hrs 50 min 0 sec
    C000       -  Initialized Solver Class,	  0.000 sec
    C000   - Reading-file-00  demoHindcastSchism3D.nc, steps in file  24, steps  available 000:023, reading  24 of 24 steps,  for hydo-model time steps 00:23,  from file offsets 00:23,  into ring buffer offsets 000:023 
    C000       -  read  24 time steps in  1.2 sec
    C000 00% step 0000:H0000b00-01 Day +00 00:00 2017-01-01 00:30:00: Rel.:   1,000: Active:01000 M:01000 S:00000  B:00000 D:000 O:00 N:000 Buffer:1000 -  0% step time = 8044.9 ms
    C000 04% step 0006:H0001b01-02 Day +00 01:00 2017-01-01 01:30:00: Rel.:   4,000: Active:04000 M:03998 S:00000  B:00002 D:000 O:00 N:000 Buffer:4000 -  1% step time =  4.7 ms
    C000 09% step 0012:H0002b02-03 Day +00 02:00 2017-01-01 02:30:00: Rel.:   7,000: Active:07000 M:06980 S:00000  B:00020 D:000 O:00 N:000 Buffer:7000 -  1% step time =  6.5 ms
    C000 13% step 0018:H0003b03-04 Day +00 03:00 2017-01-01 03:30:00: Rel.:  10,000: Active:10000 M:09953 S:00000  B:00047 D:000 O:00 N:000 Buffer:10000 -  2% step time =  8.6 ms
    C000 18% step 0024:H0004b04-05 Day +00 04:00 2017-01-01 04:30:00: Rel.:  13,000: Active:13000 M:12931 S:00000  B:00069 D:000 O:00 N:000 Buffer:13000 -  3% step time = 10.4 ms
    C000 22% step 0030:H0005b05-06 Day +00 05:00 2017-01-01 05:30:00: Rel.:  16,000: Active:16000 M:15861 S:00000  B:00139 D:000 O:00 N:000 Buffer:16000 -  3% step time = 12.1 ms
    C000 26% step 0036:H0006b06-07 Day +00 06:00 2017-01-01 06:30:00: Rel.:  19,000: Active:19000 M:18768 S:00000  B:00232 D:000 O:00 N:000 Buffer:19000 -  4% step time = 13.0 ms
    C000 31% step 0042:H0007b07-08 Day +00 07:00 2017-01-01 07:30:00: Rel.:  22,000: Active:22000 M:21510 S:00000  B:00490 D:000 O:00 N:000 Buffer:22000 -  4% step time = 15.0 ms
    C000 35% step 0048:H0008b08-09 Day +00 08:00 2017-01-01 08:30:00: Rel.:  25,000: Active:25000 M:24001 S:00000  B:00999 D:000 O:00 N:000 Buffer:25000 -  5% step time = 16.7 ms
    C000 39% step 0054:H0009b09-10 Day +00 09:00 2017-01-01 09:30:00: Rel.:  28,000: Active:28000 M:26458 S:00000  B:01542 D:000 O:00 N:000 Buffer:28000 -  6% step time = 18.2 ms
    C000 44% step 0060:H0010b10-11 Day +00 10:00 2017-01-01 10:30:00: Rel.:  31,000: Active:31000 M:29281 S:00000  B:01719 D:000 O:00 N:000 Buffer:31000 -  6% step time = 19.7 ms
    C000 48% step 0066:H0011b11-12 Day +00 11:00 2017-01-01 11:30:00: Rel.:  34,000: Active:34000 M:32090 S:00000  B:01910 D:000 O:00 N:000 Buffer:34000 -  7% step time = 21.2 ms
    C000 53% step 0072:H0012b12-13 Day +00 12:00 2017-01-01 12:30:00: Rel.:  37,000: Active:37000 M:34975 S:00000  B:02025 D:000 O:00 N:000 Buffer:37000 -  7% step time = 22.9 ms
    C000 57% step 0078:H0013b13-14 Day +00 13:00 2017-01-01 13:30:00: Rel.:  40,000: Active:40000 M:38011 S:00000  B:01989 D:000 O:00 N:000 Buffer:40000 -  8% step time = 24.5 ms
    C000 61% step 0084:H0014b14-15 Day +00 14:00 2017-01-01 14:30:00: Rel.:  43,000: Active:43000 M:40848 S:00115  B:02037 D:000 O:00 N:000 Buffer:43000 -  9% step time = 26.2 ms
    C000 66% step 0090:H0015b15-16 Day +00 15:00 2017-01-01 15:30:00: Rel.:  46,000: Active:46000 M:43211 S:00696  B:02093 D:000 O:00 N:000 Buffer:46000 -  9% step time = 26.9 ms
    C000 70% step 0096:H0016b16-17 Day +00 16:00 2017-01-01 16:30:00: Rel.:  49,000: Active:49000 M:46131 S:00696  B:02173 D:000 O:00 N:000 Buffer:49000 - 10% step time = 29.6 ms
    C000 74% step 0102:H0017b17-18 Day +00 17:00 2017-01-01 17:30:00: Rel.:  52,000: Active:52000 M:49021 S:00696  B:02283 D:000 O:00 N:000 Buffer:52000 - 10% step time = 30.9 ms
    C000 79% step 0108:H0018b18-19 Day +00 18:00 2017-01-01 18:30:00: Rel.:  55,000: Active:55000 M:51769 S:00696  B:02535 D:000 O:00 N:000 Buffer:55000 - 11% step time = 30.5 ms
    C000 83% step 0114:H0019b19-20 Day +00 19:00 2017-01-01 19:30:00: Rel.:  58,000: Active:58000 M:54369 S:00696  B:02935 D:000 O:00 N:000 Buffer:58000 - 12% step time = 32.7 ms
    C000 88% step 0120:H0020b20-21 Day +00 20:00 2017-01-01 20:30:00: Rel.:  61,000: Active:61000 M:56785 S:00696  B:03519 D:000 O:00 N:000 Buffer:61000 - 12% step time = 35.1 ms
    C000 92% step 0126:H0021b21-22 Day +00 21:00 2017-01-01 21:30:00: Rel.:  64,000: Active:64000 M:59771 S:00076  B:04153 D:000 O:00 N:000 Buffer:64000 - 13% step time = 36.6 ms
    C000 96% step 0132:H0022b22-23 Day +00 22:00 2017-01-01 22:30:00: Rel.:  67,000: Active:67000 M:62131 S:00000  B:04869 D:000 O:00 N:000 Buffer:67000 - 13% step time = 38.2 ms
    C000 100% step 0137:H0022b22-23 Day +00 22:50 2017-01-01 23:20:00: Rel.:  69,000: Active:69000 M:63605 S:00000  B:05395 D:000 O:00 N:000 Buffer:69000 - 14% step time = 48.1 ms
    C000 >>> Note: Hydro-model is "3D"  type "SCHISMreaderNCDF"
    C000       hint: Files found dir and sub-dirs of "../demos/demo_hindcast"
    C000 >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    C000 >>> Note: Found vertical diffusivity profile in hydro-model files
    C000 >>> Note: Using vertical diffusivity profile in hydro-model for vertical random walk
    C000 >>> Warning: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 >>> Warning: Making scheduler: update interval rounded to be integer number of time steps
    C000       hint: 900 sec. rounded to model time step = 1200 sec.
    C000       in:  adding scheduler
    C000 --------------------------------------------------------------------------
    C000   - Finished case number   0,  heat_map_example started: 2024-03-20 14:25:46.534260, ended: 2024-03-20 14:26:03.925328
    C000       Elapsed time =0:00:17.391068
    C000 --------------------------------------------------------------------------
    Main     >>> Note: run summary with case file names   "heat_map_example_runInfo.json"
    Main     >>> Note: to help with debugging, parameters as given by user  are in "heat_map_example_raw_user_params.json"
    Main     >>> Note: run summary with case file names   "heat_map_example_runInfo.json"
    Main >>> Warning: Deleted contents of existing output dir
    Main --------------------------------------------------------------------------
    Main OceanTracker summary:  elapsed time =0:00:18.451895
    Main       Cases -   0 errors,   4 warnings,   5 notes, check above
    Main       Main  -   0 errors,   1 warnings,   2 notes, check above
    Main --------------------------------------------------------------------------
    

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
    from read_oceantracker.python import read_ncdf_output_files, load_output_files
    from plot_oceantracker import plot_statistics
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

    raw_stats dict_keys(['total_num_particles_released', 'release_groupID_my_release_point', 'dimensions', 'limits', 'release_groupID', 'release_locations', 'release_points', 'sum_a_pollutant', 'number_of_release_points', 'time', 'x', 'num_released_total', 'count', 'count_all_particles', 'grid_cell_area', 'is_polygon_release', 'number_released_each_release_group', 'y', 'time_var', 'date', 'stats_type', 'connectivity_matrix', 'a_pollutant'])
    stats dict_keys(['total_num_particles_released', 'release_groupID_my_release_point', 'dimensions', 'limits', 'release_groupID', 'release_locations', 'release_points', 'sum_a_pollutant', 'number_of_release_points', 'time', 'x', 'num_released_total', 'count', 'count_all_particles', 'grid_cell_area', 'is_polygon_release', 'number_released_each_release_group', 'y', 'time_var', 'date', 'stats_type', 'connectivity_matrix', 'a_pollutant', 'info', 'params', 'release_group_centered_grids', 'particle_status_flags', 'particle_release_groups', 'full_case_params', 'grid'])
    animate_heat_map> colour axis limits [0, 1376] [0, 1376]
    


.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_4_1.png


.. parsed-literal::

    animate_heat_map> colour axis limits [1.4321606718741004e-07, 1000.0] [1.4321606718741004e-07, 1000.0]
    


.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_4_3.png



.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_4_4.png




.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_4_5.png



Polygon example
---------------

add polygon stats example with plotting
=======================================

.. code:: ipython3

    # Polygon Statistics example.py run using dictionary of parameters
    #------------------------------------------------
    from oceantracker import main
    params={}
    params.update(output_file_base='polygon_connectivity_map_example',  # name used as base for output files
                root_output_dir= 'output',             #  output is put in dir   'root_output_dir'\\'output_file_base'
                time_step= 600., #  10 min time step as seconds
                write_tracks = False # particle tracks not needed for on fly 
                   )
    
    # ot.set_class, sets parameters for a named class
    params.update(reader= { 'input_dir': '../demos/demo_hindcast',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                        'file_mask':  'demoHindcastSchism*.nc'})  # hindcast file mask
    params.update(release_groups= {},particle_statistics={} )
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

    Main --------------------------------------------------------------------------
    Main OceanTracker starting main:
    Main   - Output dir set up.
    Main >>> Warning: Deleted contents of existing output dir
    Main     >>> Note: to help with debugging, parameters as given by user  are in "polygon_connectivity_map_example_raw_user_params.json"
    Main   Output is in dir "e:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\polygon_connectivity_map_example"
    Main         hint: see for copies of screen output and user supplied parameters, plus all other output
    Main --------------------------------------------------------------------------
    Main  OceanTracker version 0.5.0.000 2024-03-07 - preliminary setup
    Main      Python version: 3.10.10 | packaged by conda-forge | (main, Mar 24 2023, 20:00:38) [MSC v.1934 64 bit (AMD64)]
    Main   - Found input dir "../demos/demo_hindcast"
    Main   - found hydro-model files of type  "SCHISIM"
    Main       -  sorted hyrdo-model files in time order,	  0.025 sec
    C000 --------------------------------------------------------------------------
    C000 Starting case number   0,  polygon_connectivity_map_example at 2024-03-20T14:32:20.527679
    C000 --------------------------------------------------------------------------
    C000       -  Scanned OceanTracker to build short name map to the full class_names,	  0.019 sec
    C000   - Starting grid setup
    C000       -  built node to triangles map,	  0.000 sec
    C000       -  built triangle adjacency matrix,	  0.000 sec
    C000       -  found boundary triangles,	  0.000 sec
    C000       -  built domain and island outlines,	  0.527 sec
    C000       -  calculated triangle areas,	  0.000 sec
    C000   - Finished grid setup
    C000 >>> Note: Hydro-model is "3D"  type "SCHISMreaderNCDF"
    C000       hint: Files found dir and sub-dirs of "../demos/demo_hindcast"
    C000     grid bounding box = [1590046.0 5478274.0] to [1603253.0 5492492.0]
    C000       -  built barycentric-transform matrix,	  0.000 sec
    C000 >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    C000 >>> Note: Found vertical diffusivity profile in hydro-model files
    C000 >>> Note: Using vertical diffusivity profile in hydro-model for vertical random walk
    C000 >>> Warning: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 >>> Warning: Making scheduler: update interval rounded to be integer number of time steps
    C000       hint: 900 sec. rounded to model time step = 1200 sec.
    C000       in:  adding scheduler
    C000       -  Set up run start and end times, plus release groups and their schedulers,	  0.000 sec
    C000       -  final set up of core classes,	  0.002 sec
    C000 --------------------------------------------------------------------------
    C000   - Starting polygon_connectivity_map_example,  duration: 0 days 22 hrs 50 min 0 sec
    C000       -  Initialized Solver Class,	  0.000 sec
    C000   - Reading-file-00  demoHindcastSchism3D.nc, steps in file  24, steps  available 000:023, reading  24 of 24 steps,  for hydo-model time steps 00:23,  from file offsets 00:23,  into ring buffer offsets 000:023 
    C000       -  read  24 time steps in  0.0 sec
    C000 00% step 0000:H0000b00-01 Day +00 00:00 2017-01-01 00:30:00: Rel.:   1,000: Active:01000 M:01000 S:00000  B:00000 D:000 O:00 N:000 Buffer:1000 -  0% step time = 1031.2 ms
    C000 04% step 0006:H0001b01-02 Day +00 01:00 2017-01-01 01:30:00: Rel.:   4,000: Active:04000 M:03998 S:00000  B:00002 D:000 O:00 N:000 Buffer:4000 -  1% step time =  4.2 ms
    C000 09% step 0012:H0002b02-03 Day +00 02:00 2017-01-01 02:30:00: Rel.:   7,000: Active:07000 M:06982 S:00000  B:00018 D:000 O:00 N:000 Buffer:7000 -  1% step time =  6.2 ms
    C000 13% step 0018:H0003b03-04 Day +00 03:00 2017-01-01 03:30:00: Rel.:  10,000: Active:10000 M:09967 S:00000  B:00033 D:000 O:00 N:000 Buffer:10000 -  2% step time =  8.2 ms
    C000 18% step 0024:H0004b04-05 Day +00 04:00 2017-01-01 04:30:00: Rel.:  13,000: Active:13000 M:12913 S:00000  B:00087 D:000 O:00 N:000 Buffer:13000 -  3% step time = 10.0 ms
    C000 22% step 0030:H0005b05-06 Day +00 05:00 2017-01-01 05:30:00: Rel.:  16,000: Active:16000 M:15877 S:00000  B:00123 D:000 O:00 N:000 Buffer:16000 -  3% step time = 11.5 ms
    C000 26% step 0036:H0006b06-07 Day +00 06:00 2017-01-01 06:30:00: Rel.:  19,000: Active:19000 M:18792 S:00000  B:00208 D:000 O:00 N:000 Buffer:19000 -  4% step time = 12.9 ms
    C000 31% step 0042:H0007b07-08 Day +00 07:00 2017-01-01 07:30:00: Rel.:  22,000: Active:22000 M:21452 S:00000  B:00548 D:000 O:00 N:000 Buffer:22000 -  4% step time = 14.7 ms
    C000 35% step 0048:H0008b08-09 Day +00 08:00 2017-01-01 08:30:00: Rel.:  25,000: Active:25000 M:23993 S:00000  B:01007 D:000 O:00 N:000 Buffer:25000 -  5% step time = 16.3 ms
    C000 39% step 0054:H0009b09-10 Day +00 09:00 2017-01-01 09:30:00: Rel.:  28,000: Active:28000 M:26468 S:00000  B:01532 D:000 O:00 N:000 Buffer:28000 -  6% step time = 17.5 ms
    C000 44% step 0060:H0010b10-11 Day +00 10:00 2017-01-01 10:30:00: Rel.:  31,000: Active:31000 M:29323 S:00000  B:01677 D:000 O:00 N:000 Buffer:31000 -  6% step time = 19.1 ms
    C000 48% step 0066:H0011b11-12 Day +00 11:00 2017-01-01 11:30:00: Rel.:  34,000: Active:34000 M:32078 S:00000  B:01922 D:000 O:00 N:000 Buffer:34000 -  7% step time = 20.6 ms
    C000 53% step 0072:H0012b12-13 Day +00 12:00 2017-01-01 12:30:00: Rel.:  37,000: Active:37000 M:34953 S:00000  B:02047 D:000 O:00 N:000 Buffer:37000 -  7% step time = 22.1 ms
    C000 57% step 0078:H0013b13-14 Day +00 13:00 2017-01-01 13:30:00: Rel.:  40,000: Active:40000 M:37987 S:00000  B:02013 D:000 O:00 N:000 Buffer:40000 -  8% step time = 24.0 ms
    C000 61% step 0084:H0014b14-15 Day +00 14:00 2017-01-01 14:30:00: Rel.:  43,000: Active:43000 M:40880 S:00112  B:02008 D:000 O:00 N:000 Buffer:43000 -  9% step time = 25.8 ms
    C000 66% step 0090:H0015b15-16 Day +00 15:00 2017-01-01 15:30:00: Rel.:  46,000: Active:46000 M:43222 S:00685  B:02093 D:000 O:00 N:000 Buffer:46000 -  9% step time = 26.7 ms
    C000 70% step 0096:H0016b16-17 Day +00 16:00 2017-01-01 16:30:00: Rel.:  49,000: Active:49000 M:46198 S:00685  B:02117 D:000 O:00 N:000 Buffer:49000 - 10% step time = 29.1 ms
    C000 74% step 0102:H0017b17-18 Day +00 17:00 2017-01-01 17:30:00: Rel.:  52,000: Active:52000 M:48915 S:00685  B:02400 D:000 O:00 N:000 Buffer:52000 - 10% step time = 30.1 ms
    C000 79% step 0108:H0018b18-19 Day +00 18:00 2017-01-01 18:30:00: Rel.:  55,000: Active:55000 M:51584 S:00685  B:02731 D:000 O:00 N:000 Buffer:55000 - 11% step time = 30.3 ms
    C000 83% step 0114:H0019b19-20 Day +00 19:00 2017-01-01 19:30:00: Rel.:  58,000: Active:58000 M:54283 S:00685  B:03032 D:000 O:00 N:000 Buffer:58000 - 12% step time = 32.2 ms
    C000 88% step 0120:H0020b20-21 Day +00 20:00 2017-01-01 20:30:00: Rel.:  61,000: Active:61000 M:56846 S:00685  B:03469 D:000 O:00 N:000 Buffer:61000 - 12% step time = 34.1 ms
    C000 92% step 0126:H0021b21-22 Day +00 21:00 2017-01-01 21:30:00: Rel.:  64,000: Active:64000 M:59746 S:00072  B:04182 D:000 O:00 N:000 Buffer:64000 - 13% step time = 35.8 ms
    C000 96% step 0132:H0022b22-23 Day +00 22:00 2017-01-01 22:30:00: Rel.:  67,000: Active:67000 M:62035 S:00000  B:04965 D:000 O:00 N:000 Buffer:67000 - 13% step time = 37.0 ms
    C000 100% step 0137:H0022b22-23 Day +00 22:50 2017-01-01 23:20:00: Rel.:  69,000: Active:69000 M:63656 S:00000  B:05344 D:000 O:00 N:000 Buffer:69000 - 14% step time = 45.6 ms
    C000 >>> Note: Hydro-model is "3D"  type "SCHISMreaderNCDF"
    C000       hint: Files found dir and sub-dirs of "../demos/demo_hindcast"
    C000 >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    C000 >>> Note: Found vertical diffusivity profile in hydro-model files
    C000 >>> Note: Using vertical diffusivity profile in hydro-model for vertical random walk
    C000 >>> Note: Hydro-model is "3D"  type "SCHISMreaderNCDF"
    C000       hint: Files found dir and sub-dirs of "../demos/demo_hindcast"
    C000 >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    C000 >>> Note: Found vertical diffusivity profile in hydro-model files
    C000 >>> Note: Using vertical diffusivity profile in hydro-model for vertical random walk
    C000 >>> Warning: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 >>> Warning: Making scheduler: update interval rounded to be integer number of time steps
    C000       hint: 900 sec. rounded to model time step = 1200 sec.
    C000       in:  adding scheduler
    C000 >>> Warning: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 >>> Warning: Making scheduler: update interval rounded to be integer number of time steps
    C000       hint: 900 sec. rounded to model time step = 1200 sec.
    C000       in:  adding scheduler
    C000 --------------------------------------------------------------------------
    C000   - Finished case number   0,  polygon_connectivity_map_example started: 2024-03-20 14:32:20.526679, ended: 2024-03-20 14:32:27.931390
    C000       Elapsed time =0:00:07.404711
    C000 --------------------------------------------------------------------------
    Main     >>> Note: run summary with case file names   "polygon_connectivity_map_example_runInfo.json"
    Main     >>> Note: to help with debugging, parameters as given by user  are in "heat_map_example_raw_user_params.json"
    Main     >>> Note: run summary with case file names   "heat_map_example_runInfo.json"
    Main     >>> Note: to help with debugging, parameters as given by user  are in "polygon_connectivity_map_example_raw_user_params.json"
    Main     >>> Note: run summary with case file names   "polygon_connectivity_map_example_runInfo.json"
    Main >>> Warning: Deleted contents of existing output dir
    Main >>> Warning: Deleted contents of existing output dir
    Main --------------------------------------------------------------------------
    Main OceanTracker summary:  elapsed time =0:00:07.579921
    Main       Cases -   0 errors,   8 warnings,  10 notes, check above
    Main       Main  -   0 errors,   2 warnings,   4 notes, check above
    Main --------------------------------------------------------------------------
    

Read polygon/connectivity statistics
------------------------------------

.. code:: ipython3

    #Read polygon stats and calculate connectivity matrix 
    from read_oceantracker.python import load_output_files
    
    poly_stats_data = load_output_files.load_stats_data(poly_case_info_file_name,'my_polygon')
    print('stats',poly_stats_data.keys())
    
    import matplotlib.pyplot as plt
    plt.plot(poly_stats_data['date'], poly_stats_data['connectivity_matrix'][:,0,0])
    plt.title('Connectivity time series between release point and polygon')
    
    #print(poly_stats_data['date'])


.. parsed-literal::

    stats dict_keys(['total_num_particles_released', 'release_groupID_my_release_point', 'dimensions', 'limits', 'release_groupID', 'release_locations', 'time', 'number_released_each_release_group', 'number_of_release_points', 'release_points', 'is_polygon_release', 'count_all_particles', 'num_released_total', 'count', 'time_var', 'date', 'stats_type', 'connectivity_matrix', 'info', 'params', 'release_group_centered_grids', 'polygon_list', 'particle_status_flags', 'particle_release_groups', 'full_case_params', 'grid'])
    



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

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

- Decaying particle property, eg. breakdown of a pollutant
- Gridded time series of particle statistics as heat maps, which also
  builds a heat map of the pollutant
- Plot the particle counts and pollutant as animated heatmap.

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
    ot.add_class('reader',input_dir=  '../demos/demo_hindcast/schsim3D',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                          file_mask=  'demo_hindcast_schisim3D*.nc')  # hindcast file mask
    
    # add one release locations 
    ot.add_class('release_groups', 
                   name='my_release_point', # optional name used to refere to group in plotting
                    points= [ [1599000, 5486200]],       # ust be 1 by N list pairs of release locations
                    release_interval= 900,           # seconds between releasing particles
                    pulse_size= 1000,                   # number of particles released each release_interval
                )
    # add a decaying particle property
    # add and Age decay particle property, with exponential decay based on age, with time scale 1 hour                             
    ot.add_class('particle_properties', # add a new property to particle_properties role
                name ='a_pollutant', # must have a user given name to 
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

    helper ----------------------------------------------------------------------
    helper Starting OceanTracker helper class
    helper   - Starting run using helper class
    Main      Python version: 3.10.9 | packaged by conda-forge | (main, Jan 11 2023, 15:15:40) [MSC v.1916 64 bit (AMD64)]
    Main ----------------------------------------------------------------------
    Main OceanTracker starting main:
    Main     Starting package set up
    Main         -  Built OceanTracker package tree,	  0.566 sec
    Main         -  Built OceanTracker sort name map,	  0.000 sec
    Main     -  Done package set up to setup ClassImporter,	  0.566 sec
    Main >>> Warning: Deleted contents of existing output dir
    Main Output is in dir "f:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\heat_map_example"
    Main       hint: see for copies of screen output and user supplied parameters, plus all other output
    Main     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    Main ----------------------------------------------------------------------
    Main  OceanTracker version 0.50.0010-2024-03-30 - preliminary setup
    Main   - Found input dir "../demos/demo_hindcast/schsim3D"
    Main   - found hydro-model files of type  "SCHISM"
    Main Cataloging hindcast with 1 files in dir ../demos/demo_hindcast/schsim3D
    Main     -  Cataloged hydro-model files/variables in time order,	  0.007 sec
    Main >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    Main     -  sorted hyrdo-model files in time order,	  0.033 sec
    prelim:     Starting package set up
    prelim:         -  Built OceanTracker package tree,	  0.010 sec
    prelim:         -  Built OceanTracker sort name map,	  0.000 sec
    prelim:     -  Done package set up to setup ClassImporter,	  0.010 sec
    C000 ----------------------------------------------------------------------
    C000 Starting case number   0,  heat_map_example at 2024-09-06T07:36:22.428531
    C000 ----------------------------------------------------------------------
    C000     -  Scanned OceanTracker to build short name map to the full class_names,	  0.000 sec
    C000 >>> Note: Hydro-model is "3D"  type "SCHISMreaderNCDF"
    C000       hint: Files found dir and sub-dirs of "../demos/demo_hindcast/schsim3D"
    C000     Start: 2017-01-01T00:30:00.000000000  end:  2017-01-01T23:30:00.000000000, time steps  24 
    C000     grid bounding box = [1589789.0 5479437.0] to [1603398.0 5501640.0]
    C000   - Starting grid setup
    C000     -  built node to triangles map,	  0.421 sec
    C000     -  built triangle adjacency matrix,	  0.149 sec
    C000     -  found boundary triangles,	  0.000 sec
    C000     -  built domain and island outlines,	  0.912 sec
    C000     -  calculated triangle areas,	  0.000 sec
    C000   - Finished grid setup
    C000     -  built barycentric-transform matrix,	  0.252 sec
    C000 >>> Note: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000     -  Setup field group manager,	  0.255 sec
    C000     -  Added release groups and found run start and end times,	  0.001 sec
    C000     -  Done initial setup of all classes,	  0.294 sec
    C000 >>> Note: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 ----------------------------------------------------------------------
    C000   - Starting heat_map_example,  duration: 0 days 23 hrs 0 min 0 sec
    C000   -  Reading 24 time steps,  for hindcast time steps 00:23,  into ring buffer offsets 000:023 
    C000       -  read  24 time steps in  0.8 sec
    C000 ----------------------------------------------------------------------
    C000   - Starting time stepping: 2017-01-01T00:30:00 to 2017-01-01T23:30:00 , duration  0 days 23 hrs 0 min 0 sec 
    C000 00% step 0000:H0000b00-01 Day +00 00:00 2017-01-01 00:30:00: Rel.:   1,000: Active:01000 M:01000 S:00000  B:00000 D:000 O:00 N:000 Buffer:1000   0% step time = 4424.9 ms
    C000 04% step 0006:H0001b01-02 Day +00 01:00 2017-01-01 01:30:00: Rel.:   4,000: Active:04000 M:04000 S:00000  B:00000 D:000 O:00 N:000 Buffer:4000   1% step time =  1.7 ms
    C000 09% step 0012:H0002b02-03 Day +00 02:00 2017-01-01 02:30:00: Rel.:   7,000: Active:07000 M:07000 S:00000  B:00000 D:000 O:00 N:000 Buffer:7000   1% step time =  1.9 ms
    C000 13% step 0018:H0003b03-04 Day +00 03:00 2017-01-01 03:30:00: Rel.:  10,000: Active:10000 M:09999 S:00000  B:00001 D:000 O:00 N:000 Buffer:10000   2% step time =  2.2 ms
    C000 17% step 0024:H0004b04-05 Day +00 04:00 2017-01-01 04:30:00: Rel.:  13,000: Active:13000 M:13000 S:00000  B:00000 D:000 O:00 N:000 Buffer:13000   3% step time =  2.6 ms
    C000 22% step 0030:H0005b05-06 Day +00 05:00 2017-01-01 05:30:00: Rel.:  16,000: Active:16000 M:15999 S:00000  B:00001 D:000 O:00 N:000 Buffer:16000   3% step time =  2.7 ms
    C000 26% step 0036:H0006b06-07 Day +00 06:00 2017-01-01 06:30:00: Rel.:  19,000: Active:19000 M:18999 S:00000  B:00001 D:000 O:00 N:000 Buffer:19000   4% step time =  2.9 ms
    C000 30% step 0042:H0007b07-08 Day +00 07:00 2017-01-01 07:30:00: Rel.:  22,000: Active:22000 M:21991 S:00000  B:00009 D:000 O:00 N:000 Buffer:22000   4% step time =  3.1 ms
    C000 35% step 0048:H0008b08-09 Day +00 08:00 2017-01-01 08:30:00: Rel.:  25,000: Active:25000 M:24981 S:00000  B:00019 D:000 O:00 N:000 Buffer:25000   5% step time =  4.8 ms
    C000 39% step 0054:H0009b09-10 Day +00 09:00 2017-01-01 09:30:00: Rel.:  28,000: Active:28000 M:27985 S:00000  B:00015 D:000 O:00 N:000 Buffer:28000   6% step time =  4.1 ms
    C000 43% step 0060:H0010b10-11 Day +00 10:00 2017-01-01 10:30:00: Rel.:  31,000: Active:31000 M:30983 S:00000  B:00017 D:000 O:00 N:000 Buffer:31000   6% step time =  4.7 ms
    C000 48% step 0066:H0011b11-12 Day +00 11:00 2017-01-01 11:30:00: Rel.:  34,000: Active:34000 M:33991 S:00000  B:00009 D:000 O:00 N:000 Buffer:34000   7% step time =  5.1 ms
    C000 52% step 0072:H0012b12-13 Day +00 12:00 2017-01-01 12:30:00: Rel.:  37,000: Active:37000 M:36991 S:00000  B:00009 D:000 O:00 N:000 Buffer:37000   7% step time =  4.5 ms
    C000 57% step 0078:H0012b12-13 Day +00 13:00 2017-01-01 13:30:00: Rel.:  40,000: Active:40000 M:39989 S:00000  B:00011 D:000 O:00 N:000 Buffer:40000   8% step time =  4.8 ms
    C000 61% step 0084:H0014b14-15 Day +00 14:00 2017-01-01 14:30:00: Rel.:  43,000: Active:43000 M:42992 S:00001  B:00007 D:000 O:00 N:000 Buffer:43000   9% step time =  4.9 ms
    C000 65% step 0090:H0015b15-16 Day +00 15:00 2017-01-01 15:30:00: Rel.:  46,000: Active:46000 M:45989 S:00008  B:00003 D:000 O:00 N:000 Buffer:46000   9% step time =  5.8 ms
    C000 70% step 0096:H0016b16-17 Day +00 16:00 2017-01-01 16:30:00: Rel.:  49,000: Active:49000 M:48991 S:00008  B:00001 D:000 O:00 N:000 Buffer:49000  10% step time =  5.8 ms
    C000 74% step 0102:H0017b17-18 Day +00 17:00 2017-01-01 17:30:00: Rel.:  52,000: Active:52000 M:51991 S:00008  B:00001 D:000 O:00 N:000 Buffer:52000  10% step time =  6.3 ms
    C000 78% step 0108:H0018b18-19 Day +00 18:00 2017-01-01 18:30:00: Rel.:  55,000: Active:55000 M:54991 S:00008  B:00001 D:000 O:00 N:000 Buffer:55000  11% step time =  6.2 ms
    C000 83% step 0114:H0019b19-20 Day +00 19:00 2017-01-01 19:30:00: Rel.:  58,000: Active:58000 M:57992 S:00008  B:00000 D:000 O:00 N:000 Buffer:58000  12% step time =  6.3 ms
    C000 87% step 0120:H0020b20-21 Day +00 20:00 2017-01-01 20:30:00: Rel.:  61,000: Active:61000 M:60989 S:00008  B:00003 D:000 O:00 N:000 Buffer:61000  12% step time =  6.8 ms
    C000 91% step 0126:H0021b21-22 Day +00 21:00 2017-01-01 21:30:00: Rel.:  64,000: Active:64000 M:63992 S:00000  B:00008 D:000 O:00 N:000 Buffer:64000  13% step time =  7.3 ms
    C000 96% step 0132:H0022b22-23 Day +00 22:00 2017-01-01 22:30:00: Rel.:  67,000: Active:67000 M:66992 S:00000  B:00008 D:000 O:00 N:000 Buffer:67000  13% step time =  7.7 ms
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000 100% step 0138:H0023b23-00 Day +00 23:00 2017-01-01 23:30:00: Rel.:  69,000: Active:69000 M:68997 S:00000  B:00003 D:000 O:00 N:000 Buffer:69000  14% step time = 72.4 ms
    C000 >>> Note: Hydro-model is "3D"  type "SCHISMreaderNCDF"
    C000       hint: Files found dir and sub-dirs of "../demos/demo_hindcast/schsim3D"
    C000 >>> Note: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 >>> Note: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 ----------------------------------------------------------------------
    C000   - Finished case number   0,  heat_map_example started: 2024-09-06 07:36:22.428531, ended: 2024-09-06 07:36:33.784928
    C000       Computational time =0:00:11.356397
    C000 --- End case 0 -------------------------------------------------------
    End --- Summary ----------------------------------------------------------
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    End >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End >>> Warning: Deleted contents of existing output dir
    End ----------------------------------------------------------------------
    End ----------------------------------------------------------------------
    End OceanTracker summary:  elapsed time =0:00:11.968494
    End       Cases -   0 errors,   0 warnings,   3 notes, check above
    End       Main  -   0 errors,   1 warnings,   3 notes, check above
    End   Output in f:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\heat_map_example
    End ----------------------------------------------------------------------
    

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
    raw_stats = read_ncdf_output_files.read_stats_file('./output/heat_map_example/heat_map_example_stats_gridded_time_0_my_heatmap.nc')
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

    raw_stats dict_keys(['total_num_particles_released', 'dimensions', 'limits', 'variable_attributes', 'grid_cell_area', 'num_released_total', 'time', 'x', 'y', 'count', 'number_released_each_release_group', 'count_all_particles', 'sum_a_pollutant', 'global_attributes', 'time_var', 'date', 'stats_type', 'connectivity_matrix', 'a_pollutant'])
    stats dict_keys(['total_num_particles_released', 'dimensions', 'limits', 'variable_attributes', 'grid_cell_area', 'num_released_total', 'time', 'x', 'y', 'count', 'number_released_each_release_group', 'count_all_particles', 'sum_a_pollutant', 'global_attributes', 'time_var', 'date', 'stats_type', 'connectivity_matrix', 'a_pollutant', 'particle_status_flags', 'particle_release_groups', 'grid'])
    animate_heat_map> colour axis limits [0, 1146] [0, 1146]
    


.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_4_1.png


.. parsed-literal::

    animate_heat_map> colour axis limits [1.026187963170189e-07, 1000.0] [1.026187963170189e-07, 1000.0]
    


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
    # make instance of oceantracker to use to set parameters using code, then run
    ot = OceanTracker()
    
    # ot.settings method use to set basic settings
    ot.settings(output_file_base='heat_map_example', # name used as base for output files
                root_output_dir='output',             #  output is put in dir   'root_output_dir'\\'output_file_base'
                time_step= 600., #  10 min time step as seconds
                write_tracks = False # particle tracks not needed for on fly 
                )
    # ot.set_class, sets parameters for a named class
    ot.add_class('reader',input_dir=  '../demos/demo_hindcast/schsim3D',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                          file_mask=  'demo_hindcast_schisim3D*.nc')  # hindcast file mask
    
    # add one release locations 
    ot.add_class('release_groups', 
                   name='my_release_point', # optional name used to refere to group in plotting
                    points= [ [1599000, 5486200]],       # ust be 1 by N list pairs of release locations
                    release_interval= 900,           # seconds between releasing particles
                    pulse_size= 1000,                   # number of particles released each release_interval
                )
    # add a decaying particle property
    # add and Age decay particle property, with exponential decay based on age, with time scale 1 hour                             
    ot.add_class('particle_properties', # add a new property to particle_properties role
                name ='a_pollutant', # must have a user given name to 
                class_name='oceantracker.particle_properties.age_decay.AgeDecay', #  class_role is resuspension
                initial_value= 1000,
                decay_time_scale = 3600.) # time scale of age decay ie decays initial_value* exp(-age/decay_time_scale)
    
    # add a gridded particle statistic 
    ot.add_class('particle_statistics',
                   name='my_polygon',
                   class_name= 'PolygonStats2D_timeBased',
                   polygon_list = [
                            dict(points= [   [1597682.1237, 5489972.7479],# list of one or more polygons
                                     [1598604.1667, 5490275.5488],
                                     [1598886.4247, 5489464.0424],
                                     [1597917.3387, 5489000],
                                     [1597300, 5489000], [1597682.1237, 5489972.7479]]
                            )] 
                   )
    
    # run oceantracker
    poly_case_info_file_name = ot.run()
    


.. parsed-literal::

    helper ----------------------------------------------------------------------
    helper Starting OceanTracker helper class
    helper   - Starting run using helper class
    Main      Python version: 3.10.9 | packaged by conda-forge | (main, Jan 11 2023, 15:15:40) [MSC v.1916 64 bit (AMD64)]
    Main ----------------------------------------------------------------------
    Main OceanTracker starting main:
    Main     Starting package set up
    Main         -  Built OceanTracker package tree,	  0.011 sec
    Main         -  Built OceanTracker sort name map,	  0.000 sec
    Main     -  Done package set up to setup ClassImporter,	  0.012 sec
    Main >>> Warning: Deleted contents of existing output dir
    Main Output is in dir "f:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\heat_map_example"
    Main       hint: see for copies of screen output and user supplied parameters, plus all other output
    Main     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    Main ----------------------------------------------------------------------
    Main  OceanTracker version 0.50.0010-2024-03-30 - preliminary setup
    Main   - Found input dir "../demos/demo_hindcast/schsim3D"
    Main   - found hydro-model files of type  "SCHISM"
    Main Cataloging hindcast with 1 files in dir ../demos/demo_hindcast/schsim3D
    Main     -  Cataloged hydro-model files/variables in time order,	  0.008 sec
    Main >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    Main     -  sorted hyrdo-model files in time order,	  0.022 sec
    prelim:     Starting package set up
    prelim:         -  Built OceanTracker package tree,	  0.011 sec
    prelim:         -  Built OceanTracker sort name map,	  0.000 sec
    prelim:     -  Done package set up to setup ClassImporter,	  0.011 sec
    C000 ----------------------------------------------------------------------
    C000 Starting case number   0,  heat_map_example at 2024-09-06T07:54:20.095814
    C000 ----------------------------------------------------------------------
    C000     -  Scanned OceanTracker to build short name map to the full class_names,	  0.000 sec
    C000 >>> Note: Hydro-model is "3D"  type "SCHISMreaderNCDF"
    C000       hint: Files found dir and sub-dirs of "../demos/demo_hindcast/schsim3D"
    C000     Start: 2017-01-01T00:30:00.000000000  end:  2017-01-01T23:30:00.000000000, time steps  24 
    C000     grid bounding box = [1589789.0 5479437.0] to [1603398.0 5501640.0]
    C000   - Starting grid setup
    C000     -  built node to triangles map,	  0.000 sec
    C000     -  built triangle adjacency matrix,	  0.000 sec
    C000     -  found boundary triangles,	  0.000 sec
    C000     -  built domain and island outlines,	  0.376 sec
    C000     -  calculated triangle areas,	  0.000 sec
    C000   - Finished grid setup
    C000     -  built barycentric-transform matrix,	  0.000 sec
    C000 >>> Note: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000     -  Setup field group manager,	  0.003 sec
    C000     -  Added release groups and found run start and end times,	  0.001 sec
    C000     -  Done initial setup of all classes,	  0.557 sec
    C000 >>> Note: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 ----------------------------------------------------------------------
    C000   - Starting heat_map_example,  duration: 0 days 23 hrs 0 min 0 sec
    C000   -  Reading 24 time steps,  for hindcast time steps 00:23,  into ring buffer offsets 000:023 
    C000       -  read  24 time steps in  0.2 sec
    C000 ----------------------------------------------------------------------
    C000   - Starting time stepping: 2017-01-01T00:30:00 to 2017-01-01T23:30:00 , duration  0 days 23 hrs 0 min 0 sec 
    C000 00% step 0000:H0000b00-01 Day +00 00:00 2017-01-01 00:30:00: Rel.:   1,000: Active:01000 M:01000 S:00000  B:00000 D:000 O:00 N:000 Buffer:1000   0% step time = 261.4 ms
    C000 04% step 0006:H0001b01-02 Day +00 01:00 2017-01-01 01:30:00: Rel.:   4,000: Active:04000 M:04000 S:00000  B:00000 D:000 O:00 N:000 Buffer:4000   1% step time =  1.5 ms
    C000 09% step 0012:H0002b02-03 Day +00 02:00 2017-01-01 02:30:00: Rel.:   7,000: Active:07000 M:07000 S:00000  B:00000 D:000 O:00 N:000 Buffer:7000   1% step time =  1.7 ms
    C000 13% step 0018:H0003b03-04 Day +00 03:00 2017-01-01 03:30:00: Rel.:  10,000: Active:10000 M:10000 S:00000  B:00000 D:000 O:00 N:000 Buffer:10000   2% step time =  2.0 ms
    C000 17% step 0024:H0004b04-05 Day +00 04:00 2017-01-01 04:30:00: Rel.:  13,000: Active:13000 M:13000 S:00000  B:00000 D:000 O:00 N:000 Buffer:13000   3% step time =  2.3 ms
    C000 22% step 0030:H0005b05-06 Day +00 05:00 2017-01-01 05:30:00: Rel.:  16,000: Active:16000 M:15999 S:00000  B:00001 D:000 O:00 N:000 Buffer:16000   3% step time =  2.6 ms
    C000 26% step 0036:H0006b06-07 Day +00 06:00 2017-01-01 06:30:00: Rel.:  19,000: Active:19000 M:19000 S:00000  B:00000 D:000 O:00 N:000 Buffer:19000   4% step time =  2.9 ms
    C000 30% step 0042:H0007b07-08 Day +00 07:00 2017-01-01 07:30:00: Rel.:  22,000: Active:22000 M:21994 S:00000  B:00006 D:000 O:00 N:000 Buffer:22000   4% step time =  3.2 ms
    C000 35% step 0048:H0008b08-09 Day +00 08:00 2017-01-01 08:30:00: Rel.:  25,000: Active:25000 M:24981 S:00000  B:00019 D:000 O:00 N:000 Buffer:25000   5% step time =  3.6 ms
    C000 39% step 0054:H0009b09-10 Day +00 09:00 2017-01-01 09:30:00: Rel.:  28,000: Active:28000 M:27990 S:00000  B:00010 D:000 O:00 N:000 Buffer:28000   6% step time =  3.8 ms
    C000 43% step 0060:H0010b10-11 Day +00 10:00 2017-01-01 10:30:00: Rel.:  31,000: Active:31000 M:30991 S:00000  B:00009 D:000 O:00 N:000 Buffer:31000   6% step time =  4.1 ms
    C000 48% step 0066:H0011b11-12 Day +00 11:00 2017-01-01 11:30:00: Rel.:  34,000: Active:34000 M:33986 S:00000  B:00014 D:000 O:00 N:000 Buffer:34000   7% step time =  4.4 ms
    C000 52% step 0072:H0012b12-13 Day +00 12:00 2017-01-01 12:30:00: Rel.:  37,000: Active:37000 M:36986 S:00000  B:00014 D:000 O:00 N:000 Buffer:37000   7% step time =  4.7 ms
    C000 57% step 0078:H0012b12-13 Day +00 13:00 2017-01-01 13:30:00: Rel.:  40,000: Active:40000 M:39992 S:00000  B:00008 D:000 O:00 N:000 Buffer:40000   8% step time =  5.2 ms
    C000 61% step 0084:H0014b14-15 Day +00 14:00 2017-01-01 14:30:00: Rel.:  43,000: Active:43000 M:42990 S:00000  B:00010 D:000 O:00 N:000 Buffer:43000   9% step time =  5.2 ms
    C000 65% step 0090:H0015b15-16 Day +00 15:00 2017-01-01 15:30:00: Rel.:  46,000: Active:46000 M:45973 S:00021  B:00006 D:000 O:00 N:000 Buffer:46000   9% step time =  5.6 ms
    C000 70% step 0096:H0016b16-17 Day +00 16:00 2017-01-01 16:30:00: Rel.:  49,000: Active:49000 M:48974 S:00021  B:00005 D:000 O:00 N:000 Buffer:49000  10% step time =  5.9 ms
    C000 74% step 0102:H0017b17-18 Day +00 17:00 2017-01-01 17:30:00: Rel.:  52,000: Active:52000 M:51979 S:00021  B:00000 D:000 O:00 N:000 Buffer:52000  10% step time =  6.7 ms
    C000 78% step 0108:H0018b18-19 Day +00 18:00 2017-01-01 18:30:00: Rel.:  55,000: Active:55000 M:54976 S:00021  B:00003 D:000 O:00 N:000 Buffer:55000  11% step time =  6.3 ms
    C000 83% step 0114:H0019b19-20 Day +00 19:00 2017-01-01 19:30:00: Rel.:  58,000: Active:58000 M:57979 S:00021  B:00000 D:000 O:00 N:000 Buffer:58000  12% step time =  6.5 ms
    C000 87% step 0120:H0020b20-21 Day +00 20:00 2017-01-01 20:30:00: Rel.:  61,000: Active:61000 M:60976 S:00021  B:00003 D:000 O:00 N:000 Buffer:61000  12% step time =  6.7 ms
    C000 91% step 0126:H0021b21-22 Day +00 21:00 2017-01-01 21:30:00: Rel.:  64,000: Active:64000 M:63989 S:00000  B:00011 D:000 O:00 N:000 Buffer:64000  13% step time =  7.1 ms
    C000 96% step 0132:H0022b22-23 Day +00 22:00 2017-01-01 22:30:00: Rel.:  67,000: Active:67000 M:66991 S:00000  B:00009 D:000 O:00 N:000 Buffer:67000  13% step time =  7.2 ms
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000   -  Reading  1 time steps,  for hindcast time steps 23:23,  into ring buffer offsets 023:023 
    C000       -  read   1 time steps in  0.0 sec
    C000 100% step 0138:H0023b23-00 Day +00 23:00 2017-01-01 23:30:00: Rel.:  69,000: Active:69000 M:68990 S:00000  B:00010 D:000 O:00 N:000 Buffer:69000  14% step time = 75.6 ms
    C000 >>> Note: Hydro-model is "3D"  type "SCHISMreaderNCDF"
    C000       hint: Files found dir and sub-dirs of "../demos/demo_hindcast/schsim3D"
    C000 >>> Note: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 >>> Note: Hydro-model grid in metres, all cords should be in meters, e.g. release group locations, gridded_stats grid
    C000 ----------------------------------------------------------------------
    C000   - Finished case number   0,  heat_map_example started: 2024-09-06 07:54:20.080795, ended: 2024-09-06 07:54:24.432799
    C000       Computational time =0:00:04.352004
    C000 --- End case 0 -------------------------------------------------------
    End --- Summary ----------------------------------------------------------
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    End >>> Note: No bottom_stress variable in in hydro-files, using near seabed velocity to calculate friction_velocity for resuspension
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End >>> Warning: Deleted contents of existing output dir
    End ----------------------------------------------------------------------
    End ----------------------------------------------------------------------
    End OceanTracker summary:  elapsed time =0:00:04.390589
    End       Cases -   0 errors,   0 warnings,   3 notes, check above
    End       Main  -   0 errors,   1 warnings,   3 notes, check above
    End   Output in f:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\heat_map_example
    End ----------------------------------------------------------------------
    

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

    stats dict_keys(['total_num_particles_released', 'dimensions', 'limits', 'variable_attributes', 'num_released_total', 'time', 'count', 'number_released_each_release_group', 'count_all_particles', 'global_attributes', 'time_var', 'date', 'stats_type', 'polygon_list', 'connectivity_matrix', 'particle_status_flags', 'particle_release_groups', 'grid'])
    



.. parsed-literal::

    Text(0.5, 1.0, 'Connectivity time series between release point and polygon')




.. image:: G_onthefly_statistics_files%5CG_onthefly_statistics_8_2.png


Time verses Age statistics
--------------------------

Both gridded and polygon statistics come in two types, “time” and “age”.

- “time” statistics are time series, or snapshots, of particle numbers
  and particle properties at a time interval given by
  “calculation_interval” parameter. Eg. gridded stats showing how the
  heat map of a source’s plume evolves over time.

- “age” statistics are particle counts and properties binned by particle
  age. The result are age based histograms of counts or particle
  proprieties. This is useful to give numbers in each age band arriving
  at a given grid cell or polygon, from each release group. Eg. counting
  how many larvae are old enough to settle in a polygon or grid cell
  from each potential source location.


###########################
Change log
###########################

Known issues
__________________


Version 0.4.1.201 2024-01-20
_________________________

Faster and simplified internal structure

New features
--------------------

#. Most expensive step in 3D finding vertical cell is now 5 times faster, so code net 2-3 times faster, as by default regrids  3D data to uniform Sigma grid, to speed vertical cell search by factor of 5. Original slower native vertical grid short vertical walk search still available.

#. By default uses diffusivity vertical profile for A_Z in random walk if variable mapped to A_Z_profile is found in the hydro file

#. Uses bottom stress to calculate friction velocity field if variable mapped to bottom_stress is found in the hydro file, if not uses near seabed velocity

#. Now reads new Schism v5 multi-file output, where 3D fields are in separate files

#. Can auto detect if hydro-model has lat lng cords, by looking at bounds of grid coordinates,

#. Release group now has options to release at bottom or sea surface, with optional offset.These override any given z release values.

#. Floating particle trajectory  modifier, forces particles to follow free surface

#. Can now use short class_names,eg 'PolygonRelease' instead of 'oceantracker.release_groups.point_release.PolygonRelease' for OTs inbuilt classes

#. Checks full class name is of the right type/role, to prevent using a class in the wrong role

#. All on the fly stats. can restrict particle counting within given z range and also a given water depth range

#. Now exits with error if any the release group start time is outside time range of hindcast

#. Setting display_grid_at_start plots grid as a check, clicking on image will print coords in console to use as release points
Known breaking changes- ask for help if needed to transition
______________________________________________________________

#. Reader param load_fields replaces 'field_variables' param, to load variables to names used internally. These internal names may be mapped to file variables in  new  'field_variable_map'. If a special variable, eg concentration field, no map is needed.

#. z range paramter for release and sats, replaced by z_min and z_max, warning is given

#. the frozen paticle status name is now stationary, the numerical value remains the same, it is rarely used and is not the same status as stranded by tide

Internal changes
_________________

#.


Version 0.4 Major upgrade
_________________________

Major upgrade to simplify use and parameter in repose to user input. This has breaking changes, happy to help with transition. Tried to include all changes which affect use of parameters in this upgrade

Main new features
--------------------

#. tutorials/how to notebooks to help with getting started ( in draft form).
#. "helper class" to build parameters without using dictionaries, using keyword arguments of two methods of helper class.
#. "spell checker" for param names and particle property names with suggestions
#. faster start up with improved grid outline builder
#. automatically determine hindcast file type from variables in the file, if reader class_name param not given
#. FVCOM and ROMS readers working
#. optional vertical dispersion from model vertical eddy viscosity profile.
#. If no particles active, will freerun until some are released, allows particles to be released for one season per year, with a max age, and run will skip between years
#. Only have conda install instructions
#. resuspension is core role which is always added to 3D runs (with critical fic. vel=0, by default), no longer need to add as trajectory modifier nor add a friction vel field

Known breaking changes- ask for help if needed to transition
______________________________________________________________

#. new flatter parameter structure
#. solver sub-stepping replaced by time_step in seconds param
#. writer output step count replaced by update_interval time for writing
#. only use compact mode track file format, python and matlab code will still read/convert track data to rectangular output.
#. adding a resuspension trajectory modifier, or friction vel. field

Internal changes
_________________

#. reader uses ring buffer based on hindcast step mod buffer size,  needed for shared reader development


Version 0.3.03.000 2023-01-03
_____________________________________

New features
--------------------

#.  FVCOM reader built and passed tests so far
#. ROMS reade started but not workng
#. time variable grid data, eg zlevel, dry_cell flag have moved from from  reader variables to reader.grid_time_buffers

Changes
--------------------

#. non-varying grid data is shared memory amongst cases, no change to how grid variables are accessed
#. caserunner grid variables and buffers are  built from reader_build_info, as step towards developing a shared reader

Version 0.3.01.04-06, Oct 04 2022
_____________________________________

New features
--------------------

#.?? internal rebuilt of buffered reader, as step towards using ring buffer needed for share reader

Changes
--------------------

#. internal rebuilt of buffered reader, as step towards developing ring buffer for hindcast needed for share reader
#.  grid variable now attached to reader, ie si.grid is now si.classes['reader'].grid
#. changed reading of hindcast variables to normally avoid temporary copies  and be read direct into place to smooth out memory demand
#. by default x_last_good is no longer written to tracks file

Bug fixes
--------------------

#. trapped error with warning if netcdf chunk size of tracks file variable is over 4gb

Version 0.3.01.02 Sept 13 2022
________________________________

New features
--------------------

#. Added residence count particle statistic, counts number of particles still inside designated release polygon at given time inervals, . Can be used to find residence time with release polygon, eg residence time in an estuary. See new demo 10

Changes
--------------------

#. in stats classes count_staus_equal_to and count_status_greater tha, replae by 'count_status_in_range' param, see github pages
#. post proceesing plot_heat_maps module now names plot_statistics

Bug fixes
--------------------

#. ??


Version 0.3.01.00 Sept 6 2022
_____________________________

New features
--------------------

#. 3D water_velocity in bottom bin  now uses loglayer interpolation (as in schisim), by adjusting fraction of cell to make linear vertical interp behave like log layer interp
#. improved re-suspension physics
    * resuspension jump size, size is now based on friction velocity so varies with flow speed, eq 9.28 in book Lynch : particles in the coastal ocean
    * resuspension jump size is adjusted for terminal velocity/fall velocity
    * friction velocity is now a user field ( no longer a user particle_property, see below change) based on log layer in bottom cell velocity and z

#. Track animation colours dry cells, tracks_writer adds grid dry cell data to file, set tracks_writer param 'write_dry_cell_index' to false to stop writing dry cell data

Changes
--------------------

#. class AddTerminalVelocity is now TerminalVelocity in module oceantracker.velocity_modifiers.terminal_velocity
#. friction velocity is now a custom field (no longer a particle property), to do resuspension user must now add friction_velocity to custom field parameter list,eg 'fields' : [{'class_name': 'oceantracker.fields.friction_velocity.FrictionVelocity'}],
#. removed polygon release zmin, zmax params, added zrange param for both point and polygon releases, so 3D releases random in this range
#. tidied up particle release time span calc.
#. ???

Bug fixes
--------------------

#. divide by zero in depth cell search when grid has zero vertical thickness
#. fixed- could  not read uncommented hgrid.gr3 files  for open boundary data, can now read whether hgrid file is with or without trailing comments on lines giving

Version 0.3.00.23 30/7/22
_____________________________


New features
--------------------

#. added ability to split track output files into blocks with given number of time steps per file
#. added individual timers to stats, events classes written to case info file

Changes
--------------------

#. re ordered to ensue last time step is written to tracks files

Bug fixes
--------------------

#. ??




Version 0.2.774 20/7/22
_____________________________


New features
--------------------

#. polygon release only releases into wet cells, not just those inside domain
#. added pages giving full most of default parameters for each class to doc

Changes
--------------------

#. Restructured to move all core classes up one level and delete core dir
#. changes to make dir names and class names match parameter names
    * folders interpolators now interpolator, affects class imports
    * folders readers now reader, affects user class imports
    * particle_velocity and velocity_modifiers param now velocity_modifiers
    * internally interp is now interpolator


Bug fixes
--------------------

#. reintroduced a lost feature, that blocked movement of particles into dry cells


Version 0.2.772 11/7/22
_____________________________

1) Name changes for split  and cull classes and module names
2) oceantracker_main is now just main and running is now  just main.run(params)
3) move input_dir param from shared_params to a reader param 


Version 0.2.768 01/7/2022
_____________________________

1) fixed bug in calculating depth average velocity, which meant it was zero and resupension would not happen for non zero critcal frict vel
2) created _base_reader and simplified reader as basis for making a structured grid reader

Version 0.2.760, 28/6/2022
_____________________________

1. bug fix: where velocity modifiers were not being used after restructure, eg terminal velocity
2. added open boundary condition, die on exit, for schism if hgrid file is available
3. split post_processing into two sub folders, plotting and readoutputfiles, ploting is now slit into subfiles, eg plot_tracks
4. plot_tracks, fraction_to_plot, has moved to reading of output data to become load_particle_track_vars(.., fraction_to_read=0.1)
5. particle status flags 'stranded_Bytide' is now 'stranded_by_tide', 'stranded_onBottom' is 'on_bottom', values also changed, 6.   'stranded_by_tide': 3,  'on_bottom': 6, to make it easier to set  hierarchy of movement
   (this affects split status greater than a given value and "count_status_equal_to"), 
6. To make it easier for user and future proof,  status flags are now passed by name, not value, possible names are ['unknown', 'notReleased', 'bad', 'outside_domain', 'dead', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving']
7. rebuilt tidal stranding to be based on total waterdepth < min_depth, code relating to dry cells, that was used for stranding, deleted
8. merged calaculate velocity by add_modifiers into solver  core particle_velocity class now gone
9. sharedinfo.class_interators_dict is now sharedinfo.class_list_interators 
10. brought field class, eg friction velocity, into line with initialize from parameters, as for all other classes
11. total water_depth feild added automatically, using zlevels if available, otherwise tide and water depth ( as schism "tide" is not always top zlevel in dry cells)
12. added shared_params['use_numpy_random_seed'] boolean, for testing only!
13. (not yet working in linux) ?? short version of long class names eg, 'class_name': 'oceantracker.particle_release_groups.polygon_release.PolygonRelease', with the oceantracker package can optionally use class name only, eg PolygonRelease, this requires
14. added ability for any class to add the fields or particle properties they need to operate
15. particle and other numba utilities have move to util subfolder of pariticle_properties, as have field util etc...

Version 0.2.751, 22/6/2022
_____________________________

1. Addition of triangle based concentrations fields required more uniform way for coding users to cite all classes by name, (as already done for particle and fields ) , so as to use their values in altering particle behaviour, so class referencing and iteration are now split
   - All classes can now be accessed by name through self.shared_info.classes , eg self.shared_info.classes[‘solver’] or self.shared_info.classes[‘particle_properties’][‘x’],
   - Classes which don’t require a name and none is give generic  name “unnamed001” or unnamed002 etc  based on the sequence they are added in parameters
   - The ability to iterate over sets of classes and sub sets of these classes is now separated to dicts contained in self.shared_info.class_interators, eg to iterate over different types of particle properties

2. Case numbering/sequence numbering/file names numbering, eg for class lists , eg stats, events, are now more intuitive 1 base, so first stats file has index 001, not 000, and plotting needs to use nsequence = 1 to get the first
3. Plotting heatmaps and concertation fields, can now gourad shade concentration fields, which requires as conversion from face to node values in the code 
4. Param key 'user_onfly_particle_statistics' is now 'particle_statistics'
5. Param key 'user_derived_fields' is now 'fields'
6. “user”  tags of folders and params were not needed from user perspective, so all are now gone
7. Added load_output_files.get_case_info_files_from_dir(dir_name) to load all case files in folder, with None for any missing cases, optionally can select one case, with first case is case=1
8. Note run_output_folder is deted are start of run, but using shared_param “add date to folder name”  will persevere todays work in a folder tagged with date
9. All file  and module names are lower case (to avoid issues where linux is not always case sensitive, as is git which is case insensitive to file names by default, but python is case sensitive) and Classes are camel case which is a python convention
10. Almost a full check on params is now done on start up before cases are spawned
11. Error/warning handling and recording mechanics have been rewritten from scratch 
12. Plotting: animate_particles and plot_tracks now have fraction_to_plot,  which only plots a randomly chosen fraction of the tracks
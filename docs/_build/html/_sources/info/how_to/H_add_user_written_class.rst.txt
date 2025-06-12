Add your own class
==================

[This note-book is in oceantracker/tutorials_how_to/]

First create your own class create as a python file in the same diretory
as your run script. Your class must in import the base case for the role
it performs or one of its children in that role.

.. container::

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
    ot.add_class('reader',input_dir= './demo_hindcast/schsim3D',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                          file_mask=  'demo_hindcast_schisim3D*.nc')  # hindcast file mask
    # add  release locations from two points,
    #               (ie locations where particles are released at the same times and locations)
    # note : can add multiple release groups
    ot.add_class('release_groups', 
                        points= [[1595000, 5482600],        #[x,y] pairs of release locations
                                 [1599000, 5486200]],      # must be an N by 2 or 3 or list, convertible to a numpy array
                        release_interval= 3600,           # seconds between releasing particles
                        pulse_size= 10,                   # number of particles released each release_interval
                )
    
    # add user written particle property in same dir as notebook
    
    ot.add_class('particle_properties',name='on_bottom_time',
                                            class_name='my_part_prop.TimeAtStatus')
    
    # run oceantracker
    case_info_file_name = ot.run()
    
    # output now in folder output/minimal_example
    # case_info_file_name the name a json file with useful info for post processing, eg output file names
    print(case_info_file_name)
    


.. parsed-literal::

    prelim:     Starting package set up
    helper: ----------------------------------------------------------------------
    helper: Starting OceanTrackerhelper class,  version 0.50.0043-2025-03-25 
    helper:      Python version: 3.10.9 | packaged by conda-forge | (main, Jan 11 2023, 15:15:40) [MSC v.1916 64 bit (AMD64)]
    helper: ----------------------------------------------------------------------
    helper: OceanTracker version 0.50.0043-2025-03-25  starting setup helper "main.py":
    helper: Output is in dir "f:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\minimal_example"
    helper:     hint: see for copies of screen output and user supplied parameters, plus all other output
    helper:     >>> Note: to help with debugging, parameters as given by user  are in "minimal_example_raw_user_params.json"
    helper: ----------------------------------------------------------------------
    helper: Numba setup: applied settings, max threads = 32, physical cores = 32
    helper:     hint:  cache code = False, fastmath= False
    helper: ----------------------------------------------------------------------
    helper:       - Built OceanTracker package tree,	  0.809 sec
    helper:       - Built OceanTracker sort name map,	  0.000 sec
    helper:   - Done package set up to setup ClassImporter,	  0.809 sec
    setup: ----------------------------------------------------------------------
    setup:  OceanTracker version 0.50.0043-2025-03-25 
    setup:     Starting user param. runner: "minimal_example" at  2025-03-26T14:51:51.251008
    setup: ----------------------------------------------------------------------
    setup:   - Start  field group manager and readers setup
    setup:   - Found input dir "./demo_hindcast/schsim3D"
    setup:   - Detected reader class_name = "oceantracker.reader.SCHISM_reader.SCHISMreader"
    setup:     Hydro-model is "3D", type "SCHISMreader"
    setup:         hint: Files found in dir and sub-dirs of "./demo_hindcast/schsim3D"
    setup:         Geographic coords = "False" 
    setup:         Hindcast start: 2017-01-01T00:30:00  end:  2017-01-01T23:30:00
    setup:           time step = 0 days 1 hrs 0 min 0 sec, number of time steps= 24 
    setup:           grid bounding box = [1589789.000 5479437.000] to [1603398.000 5501640.000]
    setup:           has:  A_Z profile=True  bottom stress=False
    setup: ----------------------------------------------------------------------
    setup:       - Starting grid setup
    setup:       - built node to triangles map,	  0.585 sec
    setup:       - built triangle adjacency matrix,	  0.147 sec
    setup:       - found boundary triangles,	  0.000 sec
    setup:       - built domain and island outlines,	  0.920 sec
    setup:       - calculated triangle areas,	  0.000 sec
    setup:       - Finished grid setup
    setup:       - built barycentric-transform matrix,	  0.265 sec
    setup:   - Finished field group manager and readers setup,	  3.260 sec
    setup:         using: A_Z_profile = False bottom_stress = False
    setup: ----------------------------------------------------------------------
    setup:   - Added release groups and found run start and end times,	  0.004 sec
    setup:   - Done initial setup of all classes,	  0.004 sec
    setup: ----------------------------------------------------------------------
    setup:   - Starting" minimal_example,  duration: 0 days 23 hrs 0 min 0 sec
    setup:       From 2017-01-01T00:30:00 to  2017-01-01T23:30:00
    setup:   -  Reading 24 time steps,  for hindcast time steps 00:23 into ring buffer offsets 000:023 
    setup:       -  read  24 time steps in  1.1 sec, from ./demo_hindcast/schsim3D
    setup: ----------------------------------------------------------------------
    setup:   - Starting time stepping: 2017-01-01T00:30:00 to 2017-01-01T23:30:00 , duration  0 days 23 hrs 0 min 0 sec 
    S: 'TimeAtStatus' object has no attribute 'data'
    S: Traceback (most recent call last):
    S:     File "f:\h_local_drive\particletracking\oceantracker\oceantracker\oceantracker_params_runner.py", line 52, in run
    S:       case_info_file= self._run_case()
    S:     File "f:\h_local_drive\particletracking\oceantracker\oceantracker\oceantracker_params_runner.py", line 210, in _run_case
    S:       si.core_class_roles.solver.solve() # do time stepping
    S:     File "f:\h_local_drive\particletracking\oceantracker\oceantracker\solver\solver.py", line 95, in solve
    S:       new_particleIDs  = pgm.release_particles(n_time_step, time_sec)
    S:     File "f:\h_local_drive\particletracking\oceantracker\oceantracker\particle_group_manager\particle_group_manager.py", line 117, in release_particles
    S:       i.initial_value_at_birth(new_buffer_indices)
    S:     File "f:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\my_part_prop.py", line 38, in initial_value_at_birth
    S:       self.set_values(0., new_part_IDs)  # set total time to zero when born
    S:     File "f:\h_local_drive\particletracking\oceantracker\oceantracker\particle_properties\_base_particle_properties.py", line 104, in set_values
    S:       particle_operations_util.set_value(self.data, values, active)
    S:   AttributeError: 'TimeAtStatus' object has no attribute 'data'
    S:   
    S: >>> Error:  Unexpected error  
    S:     hint: check for first error above or in log file.txt or .err file 
    end: ----------------------------------------------------------------------
    end: >>> Error:  Unexpected error  
    end:     hint: check for first error above or in log file.txt or .err file 
    end: 
    end: ----------------------------------------------------------------------
    end:       Error counts -   1 errors,   0 warnings,   1 notes, check above
    end: 
    end: --- Found errors, so some cases may not have completed ---------------
    end: --- see above or  *_caseLog.txt and *_caseLog.err files --------------
    end: ----------------------------------------------------------------------
    end:   - minimal_example" started: 25445.8385601, ended: 2025-03-26 14:51:59.879385
    end:       Computational time =0:00:09.629072
    end:   Output in f:\H_Local_drive\ParticleTracking\oceantracker\tutorials_how_to\output\minimal_example
    end: 
    end: --- Finished Oceantracker run ----------------------------------------
    end: 
    end: >>> Error: Fatal errors, run did not complete  
    end:     hint: check for first error above, log file.txt or .err file 
    None
    

Read and plot output
--------------------

A first basic plot of particle tracks

.. code:: ipython3

    from oceantracker.read_output.python import load_output_files
    
    # read particle track data into a dictionary using case_info_file_name
    tracks = load_output_files.load_track_data(case_info_file_name)
    print(tracks.keys()) # show what is in tracks dictionary holds
    
    from oceantracker.plot_output import plot_tracks
    
    ax= [1591000, 1601500, 5479500, 5491000]  # area to plot 
    plot_tracks.plot_tracks(tracks, axis_lims=ax, show_grid=True)


.. parsed-literal::

    loading oceantracker read files
    

::


    ---------------------------------------------------------------------------

    TypeError                                 Traceback (most recent call last)

    Cell In[3], line 4
          1 from read_oceantracker.python import load_output_files
          3 # read particle track data into a dictionary using case_info_file_name
    ----> 4 tracks = load_output_files.load_track_data(case_info_file_name)
          5 print(tracks.keys()) # show what is in tracks dictionary holds
          7 from plot_oceantracker.plot_tracks import plot_tracks
    

    File f:\h_local_drive\particletracking\oceantracker\read_oceantracker\python\load_output_files.py:34, in load_track_data(case_info_file_name, var_list, fraction_to_read, file_number, gridID)
         30 def load_track_data(case_info_file_name, var_list=None, fraction_to_read= None, file_number=None, gridID=0):
         31     # load one track file from squeuence of what may be split files
         32     # todo load split track files into  dictionary
    ---> 34     case_info = read_case_info_file(case_info_file_name)
         36     tracks = read_ncdf_output_files.read_particle_tracks_file(case_info['output_files']['tracks_writer'],
         37                                                        file_dir=case_info['output_files']['run_output_dir'],
         38                                                        var_list=var_list,
         39                                                        file_number=file_number,  fraction_to_read=fraction_to_read)
         41     tracks['grid'] = load_grid(case_info_file_name,gridID=gridID)
    

    File f:\h_local_drive\particletracking\oceantracker\read_oceantracker\python\load_output_files.py:18, in read_case_info_file(case_info_file_name)
         16     case_info = json_util.read_JSON(case_info_file_name[0])
         17 else:
    ---> 18     case_info = json_util.read_JSON(case_info_file_name)
         20 # make case info output dir consistent with given file name
         21 case_info['output_files']['run_output_dir'] = path.dirname(case_info_file_name)
    

    File f:\h_local_drive\particletracking\oceantracker\oceantracker\util\json_util.py:25, in read_JSON(file_name)
         23 def read_JSON(file_name):
         24     # avoid changing given file name
    ---> 25     file_name= path.normpath(file_name)
         26     if file_name is None or not path.isfile(file_name):
         27         print('Cannot find json file "' + file_name + '"  ')
    

    File c:\ProgramData\miniconda3\envs\otdev310\lib\ntpath.py:491, in normpath(path)
        489 def normpath(path):
        490     """Normalize path, eliminating double slashes, etc."""
    --> 491     path = os.fspath(path)
        492     if isinstance(path, bytes):
        493         sep = b'\\'
    

    TypeError: expected str, bytes or os.PathLike object, not NoneType


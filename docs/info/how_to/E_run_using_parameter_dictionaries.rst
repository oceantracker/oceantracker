Running using param. dict.
==========================

[This note-book is in oceantracker/tutorials_how_to/]

The earlier notebook showed how to set parameters and run using the
helper class. Here we exploit the flexibility to run Oceantracker
directly using a parameter dictionary built in code or read from a file.
The dictionary can be built using {‘pulse_size’:10} or dict(pulse=10)
approaches.

Build param. dict. with code
----------------------------

The below extends the minimal_example, shows two ways to build a
parameter dictionary and different ways to run OceanTracker, from code
or command line.

.. code:: ipython3

    # build a more complex dictionary of parameters using code
    params={
        'output_file_base' :'param_test1',      # name used as base for output files
        'root_output_dir':'output',             #  output is put in dir   'root_output_dir'/'output_file_base'
        'time_step' : 120,  #  2 min time step as seconds  
        'reader': dict(input_dir='../demos/demo_hindcast/schsim3D',  # folder to search for hindcast files, sub-dirs will, by default, also be searched
                      file_mask= 'demo_hindcast_schisim3D*.nc',    # the file mask of the hindcast files
                        ),
        # add a list of release groups, the release locations from two points, 
        #       particle_release_groups are a list of one or more release groups 
        #               (ie locations where particles are released at the same times and locations) 
        'release_groups': [ # class_name not uses as PointRelease is the default
                    {'name': 'my_release_point', # optional name to refer to in code
                    'points':[[1595000, 5482600],
                              [1599000, 5486200]],      # must be an N by 2 or 3 or list, convertible to a numpy array
                    'release_interval': 3600,           # seconds between releasing particles
                    'pulse_size': 10,                   # number of particles released each release_interval
                    },
                    {'class_name': 'PolygonRelease', # use a polygon release
                                        'points':[   [1597682.1237, 5489972.7479],
                                                        [1598604.1667, 5490275.5488],
                                                        [1598886.4247, 5489464.0424],
                                                        [1597917.3387, 5489000],
                                                        [1597300, 5489000], [1597682.1237, 5489972.7479]],
                                        'release_interval': 7200,           # seconds between releasing particles
                                        'pulse_size': 20,                   # number of particles released each release_interval
                                        },    
                    ],
        'resuspension' : dict(critical_friction_velocity= .005), # only re-suspend particles if friction vel. exceeds this value
        
        # list of velocity_modifiers are a set of velocities added to  water velocity give in  hydrodynamic model's 
        'velocity_modifiers' : [   # here a fall velocity with given mean and variance is added to the computation 
                    {'name':'fall_velocity', #optional name
                     'class_name' : 'TerminalVelocity', 
                     'value': -0.001,
                     'variance': 0.0002} # fall velocity has this variance around value
                            ],                      
            }
    
    # write params to build on for later examples
    from oceantracker.util import json_util, yaml_util
    json_util.write_JSON('./example_param_files/param_test1.json', params) 
    yaml_util.write_YAML('./example_param_files/param_test1.yaml', params)

### Show parameters in yaml format

yaml format has no brackets/braces and relies on tab indenting to nest
items

.. code:: ipython3

    # show the params in yaml format
    import yaml
    p = yaml_util.read_YAML('./example_param_files/param_test1.yaml')
    print( yaml.dump(p))


.. parsed-literal::

    output_file_base: param_test1
    reader:
      file_mask: demo_hindcast_schisim3D*.nc
      input_dir: ../demos/demo_hindcast/schsim3D
    release_groups:
    - name: my_release_point
      points:
      - - 1595000
        - 5482600
      - - 1599000
        - 5486200
      pulse_size: 10
      release_interval: 3600
    - class_name: PolygonRelease
      points:
      - - 1597682.1237
        - 5489972.7479
      - - 1598604.1667
        - 5490275.5488
      - - 1598886.4247
        - 5489464.0424
      - - 1597917.3387
        - 5489000
      - - 1597300
        - 5489000
      - - 1597682.1237
        - 5489972.7479
      pulse_size: 20
      release_interval: 7200
    resuspension:
      critical_friction_velocity: 0.005
    root_output_dir: output
    time_step: 120
    velocity_modifiers:
    - class_name: TerminalVelocity
      name: fall_velocity
      value: -0.001
      variance: 0.0002
    
    

Run OceanTracker from parameters
--------------------------------

There are several ways to run OceanTracker

1) By coding

   - build parameters in code and run

   - or coding to read parameter file and then run

2) Without coding

   - run from command line with parameter file which is built by editing
     a json/yaml text file

Note:

There are many ways to run the code, eg. with IDE like Pycharm, Visual
Studio Code. It can also, as here, be run in iPython notebooks. However
the way notebooks are implemented can sometimes result in issues:

- errors when running Oceantracker a second time or other unexpected
  behavior, due to shared memory space, fix by reloading the kernel

- if using note books on Windows, it is not possible to run Oceantracker
  cases in parallel, without a work around given in a later “how to”.

Run with code built params.
---------------------------

Is line below!

.. code:: ipython3

    # run oceantracker using param dict built in cells above
    from oceantracker import main
    
    case_info_file_name = main.run(params) 
    # case_info file is the name of a json file useful in plotting results 


.. parsed-literal::

    Main      Python version: 3.10.14 | packaged by conda-forge | (main, Mar 20 2024, 12:40:08) [MSC v.1938 64 bit (AMD64)]
    Main ----------------------------------------------------------------------
    Main OceanTracker starting main:
    Main     Starting package set up
    Main         -  Built OceanTracker package tree,	  1.434 sec
    Main         -  Built OceanTracker sort name map,	  0.000 sec
    Main     -  Done package set up to setup ClassImporter,	  1.434 sec
    Main Output is in dir "c:\Work\ot_install_test\oceantracker\tutorials_how_to\output\param_test1"
    Main       hint: see for copies of screen output and user supplied parameters, plus all other output
    Main     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    Main ----------------------------------------------------------------------
    Main  OceanTracker version 0.50.0009-2024-03-30 - preliminary setup
    Main   - Found input dir "../demos/demo_hindcast/schsim3D"
    Main   - found hydro-model files of type  "SCHISM"
    Main Cataloging hindcast with 1 files in dir ../demos/demo_hindcast/schsim3D
    Main     -  Cataloged hydro-model files/variables in time order,	  0.023 sec
    Main     -  sorted hyrdo-model files in time order,	  0.116 sec
    prelim:     Starting package set up
    prelim:         -  Built OceanTracker package tree,	  0.024 sec
    prelim:         -  Built OceanTracker sort name map,	  0.000 sec
    prelim:     -  Done package set up to setup ClassImporter,	  0.024 sec
    C000 ----------------------------------------------------------------------
    C000 Starting case number   0,  param_test1 at 2024-12-12T10:46:45.813781
    C000 ----------------------------------------------------------------------
    C000     -  Scanned OceanTracker to build short name map to the full class_names,	  0.000 sec
    C000 >>> Note: Hydro-model is "3D", in geographic coords = "False"  type "SCHISMreaderNCDF"
    C000       hint: Files found in dir and sub-dirs of "../demos/demo_hindcast/schsim3D"
    C000       Hindcast start: 2017-01-01T00:30:00.000000000  end:  2017-01-01T23:30:00.000000000, time steps  24 
    C000         grid bounding box = [1589789.000 5479437.000] to [1603398.000 5501640.000]
    C000   - Starting grid setup
    C000     -  built node to triangles map,	  1.991 sec
    C000     -  built triangle adjacency matrix,	  0.439 sec
    C000     -  found boundary triangles,	  0.000 sec
    C000     -  built domain and island outlines,	  3.004 sec
    C000     -  calculated triangle areas,	  0.000 sec
    C000   - Finished grid setup
    C000     -  built barycentric-transform matrix,	  0.602 sec
    C000     -  Setup field group manager,	  7.624 sec
    C000     -  Added release groups and found run start and end times,	  1.471 sec
    C000 >>> Note: When using a terminal velocity, ensure time step is small enough that vertical displacement is a small fraction of the water depth, ie vertical Courant number < 1
    C000     -  Done initial setup of all classes,	  1.345 sec
    C000 ----------------------------------------------------------------------
    C000   - Starting param_test1,  duration: 0 days 23 hrs 0 min 0 sec
    C000   -  Reading 24 time steps,  for hindcast time steps 00:23, from ..\demos\demo_hindcast\schsim3D  into ring buffer offsets 000:023 
    C000       -  read  24 time steps in  6.6 sec
    C000 ----------------------------------------------------------------------
    C000   - Starting time stepping: 2017-01-01T00:30:00 to 2017-01-01T23:30:00 , duration  0 days 23 hrs 0 min 0 sec 
    C000     -  Opened tracks output to : param_test1_tracks_compact.nc,	  0.004 sec
    C000 00% step 0000:H0000b00-01 Day +00 00:00 2017-01-01 00:30:00: Rel.:62    : Active:62     M:62     S:0       B:0      D:0      O:0      N:0      Buffer:62       0% step time = 10679.6 ms
    C000 04% step 0030:H0001b01-02 Day +00 01:00 2017-01-01 01:30:00: Rel.:82    : Active:82     M:80     S:0       B:2      D:0      O:0      N:0      Buffer:82       0% step time =  4.4 ms
    C000 09% step 0060:H0002b02-03 Day +00 02:00 2017-01-01 02:30:00: Rel.:141   : Active:141    M:137    S:0       B:4      D:0      O:0      N:0      Buffer:141      0% step time =  5.0 ms
    C000 13% step 0090:H0003b03-04 Day +00 03:00 2017-01-01 03:30:00: Rel.:161   : Active:161    M:147    S:10      B:4      D:0      O:0      N:0      Buffer:161      0% step time =  4.3 ms
    C000 17% step 0120:H0004b04-05 Day +00 04:00 2017-01-01 04:30:00: Rel.:210   : Active:210    M:193    S:10      B:7      D:0      O:0      N:0      Buffer:210      0% step time =  5.7 ms
    C000 22% step 0150:H0005b05-06 Day +00 05:00 2017-01-01 05:30:00: Rel.:230   : Active:230    M:202    S:12      B:16     D:0      O:0      N:0      Buffer:230      0% step time =  4.5 ms
    C000 26% step 0180:H0006b06-07 Day +00 06:00 2017-01-01 06:30:00: Rel.:271   : Active:271    M:241    S:12      B:18     D:0      O:0      N:0      Buffer:271      0% step time =  4.4 ms
    C000 30% step 0210:H0007b07-08 Day +00 07:00 2017-01-01 07:30:00: Rel.:291   : Active:291    M:262    S:10      B:19     D:0      O:0      N:0      Buffer:291      0% step time =  5.2 ms
    C000 35% step 0240:H0008b08-09 Day +00 08:00 2017-01-01 08:30:00: Rel.:348   : Active:348    M:318    S:10      B:20     D:0      O:0      N:0      Buffer:348      0% step time =  5.1 ms
    C000 39% step 0270:H0009b09-10 Day +00 09:00 2017-01-01 09:30:00: Rel.:368   : Active:368    M:346    S:0       B:22     D:0      O:0      N:0      Buffer:368      0% step time =  3.9 ms
    C000 43% step 0300:H0010b10-11 Day +00 10:00 2017-01-01 10:30:00: Rel.:409   : Active:409    M:387    S:0       B:22     D:0      O:0      N:0      Buffer:409      0% step time =  5.2 ms
    C000 48% step 0330:H0011b11-12 Day +00 11:00 2017-01-01 11:30:00: Rel.:429   : Active:429    M:413    S:0       B:16     D:0      O:0      N:0      Buffer:429      0% step time =  3.9 ms
    C000 52% step 0360:H0012b12-13 Day +00 12:00 2017-01-01 12:30:00: Rel.:469   : Active:469    M:454    S:0       B:15     D:0      O:0      N:0      Buffer:469      0% step time =  5.0 ms
    C000 57% step 0390:H0012b12-13 Day +00 13:00 2017-01-01 13:30:00: Rel.:489   : Active:489    M:469    S:12      B:8      D:0      O:0      N:0      Buffer:489      0% step time =  4.1 ms
    C000 61% step 0420:H0014b14-15 Day +00 14:00 2017-01-01 14:30:00: Rel.:531   : Active:531    M:507    S:13      B:11     D:0      O:0      N:0      Buffer:531      0% step time =  6.5 ms
    C000 65% step 0450:H0015b15-16 Day +00 15:00 2017-01-01 15:30:00: Rel.:551   : Active:551    M:502    S:47      B:2      D:0      O:0      N:0      Buffer:551      0% step time =  4.5 ms
    C000 70% step 0480:H0016b16-17 Day +00 16:00 2017-01-01 16:30:00: Rel.:592   : Active:592    M:532    S:55      B:5      D:0      O:0      N:0      Buffer:592      0% step time =  4.6 ms
    C000 74% step 0510:H0017b17-18 Day +00 17:00 2017-01-01 17:30:00: Rel.:612   : Active:612    M:548    S:64      B:0      D:0      O:0      N:0      Buffer:612      0% step time =  4.9 ms
    C000 78% step 0540:H0018b18-19 Day +00 18:00 2017-01-01 18:30:00: Rel.:654   : Active:654    M:590    S:64      B:0      D:0      O:0      N:0      Buffer:654      0% step time =  4.7 ms
    C000 83% step 0570:H0019b19-20 Day +00 19:00 2017-01-01 19:30:00: Rel.:674   : Active:674    M:611    S:63      B:0      D:0      O:0      N:0      Buffer:674      0% step time =  4.3 ms
    C000 87% step 0600:H0020b20-21 Day +00 20:00 2017-01-01 20:30:00: Rel.:717   : Active:717    M:660    S:55      B:2      D:0      O:0      N:0      Buffer:717      0% step time =  5.6 ms
    C000 91% step 0630:H0021b21-22 Day +00 21:00 2017-01-01 21:30:00: Rel.:737   : Active:737    M:717    S:13      B:7      D:0      O:0      N:0      Buffer:737      0% step time =  5.1 ms
    C000 96% step 0660:H0022b22-23 Day +00 22:00 2017-01-01 22:30:00: Rel.:803   : Active:803    M:777    S:12      B:14     D:0      O:0      N:0      Buffer:803      0% step time =  5.0 ms
    C000 100% step 0690:H0023b23-00 Day +00 23:00 2017-01-01 23:30:00: Rel.:803   : Active:803    M:788    S:0       B:15     D:0      O:0      N:0      Buffer:803      0% step time =  5.9 ms
    C000 >>> Note: Hydro-model is "3D", in geographic coords = "False"  type "SCHISMreaderNCDF"
    C000       hint: Files found in dir and sub-dirs of "../demos/demo_hindcast/schsim3D"
    C000 >>> Note: When using a terminal velocity, ensure time step is small enough that vertical displacement is a small fraction of the water depth, ie vertical Courant number < 1
    C000 ----------------------------------------------------------------------
    C000   - Finished case number   0,  param_test1 started: 2024-12-12 10:46:45.788354, ended: 2024-12-12 10:47:21.404230
    C000       Computational time =0:00:35.615876
    C000 --- End case 0 -------------------------------------------------------
    End --- Summary ----------------------------------------------------------
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End ----------------------------------------------------------------------
    End ----------------------------------------------------------------------
    End OceanTracker summary:  elapsed time =0:00:37.188855
    End       Cases -   0 errors,   0 warnings,   2 notes, check above
    End       Main  -   0 errors,   0 warnings,   2 notes, check above
    End   Output in c:\Work\ot_install_test\oceantracker\tutorials_how_to\output\param_test1
    End ----------------------------------------------------------------------
    

.. code:: ipython3

    # plot animation of results
    from matplotlib import pyplot as plt
    from plot_oceantracker.plot_tracks import animate_particles
    from read_oceantracker.python import  load_output_files
    from IPython.display import HTML # show animation in note book
    
    # read particle track data into a dictionary using case_info_file_name
    tracks = load_output_files.load_track_data(case_info_file_name)
    
    ax= [1591000, 1601500, 5479500, 5491000]  # area to plot
    # animate particles
    anim = animate_particles(tracks, axis_lims=ax,title='Fall vel.,  test' , 
                             show_dry_cells=True, show_grid=True, show=False) # use ipython to show video, rather than matplotlib plt.show()
    
    HTML(anim.to_html5_video())# this is slow to build!


::


    ---------------------------------------------------------------------------

    RuntimeError                              Traceback (most recent call last)

    Cell In[4], line 15
         11 # animate particles
         12 anim = animate_particles(tracks, axis_lims=ax,title='Fall vel.,  test' , 
         13                          show_dry_cells=True, show_grid=True, show=False) # use ipython to show video, rather than matplotlib plt.show()
    ---> 15 HTML(anim.to_html5_video())
    

    File c:\Users\rossv\.conda\envs\ot310\lib\site-packages\matplotlib\animation.py:1285, in Animation.to_html5_video(self, embed_limit)
       1282 path = Path(tmpdir, "temp.m4v")
       1283 # We create a writer manually so that we can get the
       1284 # appropriate size for the tag
    -> 1285 Writer = writers[mpl.rcParams['animation.writer']]
       1286 writer = Writer(codec='h264',
       1287                 bitrate=mpl.rcParams['animation.bitrate'],
       1288                 fps=1000. / self._interval)
       1289 self.save(str(path), writer=writer)
    

    File c:\Users\rossv\.conda\envs\ot310\lib\site-packages\matplotlib\animation.py:148, in MovieWriterRegistry.__getitem__(self, name)
        146 if self.is_available(name):
        147     return self._registered[name]
    --> 148 raise RuntimeError(f"Requested MovieWriter ({name}) not available")
    

    RuntimeError: Requested MovieWriter (ffmpeg) not available



.. image:: E_run_using_parameter_dictionaries_files%5CE_run_using_parameter_dictionaries_6_1.png


Run by reading param. file
--------------------------

Run from command line
---------------------

Run without coding from command lin bu using a parameter file pre-built
in a text editor.

From within an activated oceantracker conda environment, run command
line below.

On Windows, do this within an anaconda/miniconda prompt window with an
activated environment.

eg. run “run_oceantracker.py” script in the oceantracker/oceantracker
directory with command

``python  ../oceantracker/run_oceantracker.py ./example_param_files/param_test1.json``

.. code:: ipython3

    !python  ../oceantracker/run_ot_cmd_line.py ./example_param_files/param_test1.json


.. parsed-literal::

    Main      Python version: 3.10.14 | packaged by conda-forge | (main, Mar 20 2024, 12:40:08) [MSC v.1938 64 bit (AMD64)]
    Main ----------------------------------------------------------------------
    Main OceanTracker starting main:
    Main     Starting package set up
    Main         -  Built OceanTracker package tree,	  0.962 sec
    Main         -  Built OceanTracker sort name map,	  0.000 sec
    Main     -  Done package set up to setup ClassImporter,	  0.962 sec
    Main >>> Warning: Deleted contents of existing output dir
    Main Output is in dir "c:\Work\ot_install_test\oceantracker\tutorials_how_to\output\param_test1"
    Main       hint: see for copies of screen output and user supplied parameters, plus all other output
    Main     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    Main ----------------------------------------------------------------------
    Main  OceanTracker version 0.50.0009-2024-03-30 - preliminary setup
    Main   - Found input dir "../demos/demo_hindcast/schsim3D"
    Main   - found hydro-model files of type  "SCHISM"
    Main Cataloging hindcast with 1 files in dir ../demos/demo_hindcast/schsim3D
    Main     -  Cataloged hydro-model files/variables in time order,	  0.024 sec
    Main     -  sorted hyrdo-model files in time order,	  0.107 sec
    prelim:     Starting package set up
    prelim:         -  Built OceanTracker package tree,	  0.029 sec
    prelim:         -  Built OceanTracker sort name map,	  0.000 sec
    prelim:     -  Done package set up to setup ClassImporter,	  0.030 sec
    C000 ----------------------------------------------------------------------
    C000 Starting case number   0,  param_test1 at 2024-12-12T11:38:27.124392
    C000 ----------------------------------------------------------------------
    C000     -  Scanned OceanTracker to build short name map to the full class_names,	  0.000 sec
    C000 >>> Note: Hydro-model is "3D", in geographic coords = "False"  type "SCHISMreaderNCDF"
    C000       hint: Files found in dir and sub-dirs of "../demos/demo_hindcast/schsim3D"
    C000       Hindcast start: 2017-01-01T00:30:00.000000000  end:  2017-01-01T23:30:00.000000000, time steps  24 
    C000         grid bounding box = [1589789.000 5479437.000] to [1603398.000 5501640.000]
    C000   - Starting grid setup
    C000     -  built node to triangles map,	  1.414 sec
    C000     -  built triangle adjacency matrix,	  0.385 sec
    C000     -  found boundary triangles,	  0.000 sec
    C000     -  built domain and island outlines,	  2.223 sec
    C000     -  calculated triangle areas,	  0.000 sec
    C000   - Finished grid setup
    C000     -  built barycentric-transform matrix,	  0.606 sec
    C000     -  Setup field group manager,	  6.053 sec
    C000     -  Added release groups and found run start and end times,	  1.379 sec
    C000 >>> Note: When using a terminal velocity, ensure time step is small enough that vertical displacement is a small fraction of the water depth, ie vertical Courant number < 1
    C000     -  Done initial setup of all classes,	  1.481 sec
    C000 ----------------------------------------------------------------------
    C000   - Starting param_test1,  duration: 0 days 23 hrs 0 min 0 sec
    C000   -  Reading 24 time steps,  for hindcast time steps 00:23, from ..\demos\demo_hindcast\schsim3D  into ring buffer offsets 000:023 
    C000       -  read  24 time steps in  6.6 sec
    C000 ----------------------------------------------------------------------
    C000   - Starting time stepping: 2017-01-01T00:30:00 to 2017-01-01T23:30:00 , duration  0 days 23 hrs 0 min 0 sec 
    C000     -  Opened tracks output to : param_test1_tracks_compact.nc,	  0.005 sec
    C000 00% step 0000:H0000b00-01 Day +00 00:00 2017-01-01 00:30:00: Rel.:61    : Active:61     M:61     S:0       B:0      D:0      O:0      N:0      Buffer:61       0% step time = 10649.4 ms
    C000 04% step 0030:H0001b01-02 Day +00 01:00 2017-01-01 01:30:00: Rel.:81    : Active:81     M:79     S:0       B:2      D:0      O:0      N:0      Buffer:81       0% step time = 10.6 ms
    C000 09% step 0060:H0002b02-03 Day +00 02:00 2017-01-01 02:30:00: Rel.:125   : Active:125    M:119    S:0       B:6      D:0      O:0      N:0      Buffer:125      0% step time =  9.2 ms
    C000 13% step 0090:H0003b03-04 Day +00 03:00 2017-01-01 03:30:00: Rel.:145   : Active:145    M:126    S:11      B:8      D:0      O:0      N:0      Buffer:145      0% step time =  5.4 ms
    C000 17% step 0120:H0004b04-05 Day +00 04:00 2017-01-01 04:30:00: Rel.:187   : Active:187    M:169    S:11      B:7      D:0      O:0      N:0      Buffer:187      0% step time =  5.5 ms
    C000 22% step 0150:H0005b05-06 Day +00 05:00 2017-01-01 05:30:00: Rel.:207   : Active:207    M:178    S:11      B:18     D:0      O:0      N:0      Buffer:207      0% step time =  5.2 ms
    C000 26% step 0180:H0006b06-07 Day +00 06:00 2017-01-01 06:30:00: Rel.:247   : Active:247    M:218    S:11      B:18     D:0      O:0      N:0      Buffer:247      0% step time =  5.8 ms
    C000 30% step 0210:H0007b07-08 Day +00 07:00 2017-01-01 07:30:00: Rel.:267   : Active:267    M:238    S:11      B:18     D:0      O:0      N:0      Buffer:267      0% step time =  5.5 ms
    C000 35% step 0240:H0008b08-09 Day +00 08:00 2017-01-01 08:30:00: Rel.:328   : Active:328    M:299    S:11      B:18     D:0      O:0      N:0      Buffer:328      0% step time =  6.0 ms
    C000 39% step 0270:H0009b09-10 Day +00 09:00 2017-01-01 09:30:00: Rel.:348   : Active:348    M:326    S:0       B:22     D:0      O:0      N:0      Buffer:348      0% step time =  4.0 ms
    C000 43% step 0300:H0010b10-11 Day +00 10:00 2017-01-01 10:30:00: Rel.:403   : Active:403    M:378    S:0       B:25     D:0      O:0      N:0      Buffer:403      0% step time =  5.4 ms
    C000 48% step 0330:H0011b11-12 Day +00 11:00 2017-01-01 11:30:00: Rel.:423   : Active:423    M:413    S:0       B:10     D:0      O:0      N:0      Buffer:423      0% step time =  4.1 ms
    C000 52% step 0360:H0012b12-13 Day +00 12:00 2017-01-01 12:30:00: Rel.:479   : Active:479    M:460    S:0       B:19     D:0      O:0      N:0      Buffer:479      0% step time =  5.1 ms
    C000 57% step 0390:H0012b12-13 Day +00 13:00 2017-01-01 13:30:00: Rel.:499   : Active:499    M:480    S:10      B:9      D:0      O:0      N:0      Buffer:499      0% step time =  4.2 ms
    C000 61% step 0420:H0014b14-15 Day +00 14:00 2017-01-01 14:30:00: Rel.:555   : Active:555    M:530    S:13      B:12     D:0      O:0      N:0      Buffer:555      0% step time =  6.0 ms
    C000 65% step 0450:H0015b15-16 Day +00 15:00 2017-01-01 15:30:00: Rel.:575   : Active:575    M:516    S:54      B:5      D:0      O:0      N:0      Buffer:575      0% step time =  5.0 ms
    C000 70% step 0480:H0016b16-17 Day +00 16:00 2017-01-01 16:30:00: Rel.:616   : Active:616    M:550    S:58      B:8      D:0      O:0      N:0      Buffer:616      0% step time =  5.7 ms
    C000 74% step 0510:H0017b17-18 Day +00 17:00 2017-01-01 17:30:00: Rel.:636   : Active:636    M:568    S:66      B:2      D:0      O:0      N:0      Buffer:636      0% step time =  4.6 ms
    C000 78% step 0540:H0018b18-19 Day +00 18:00 2017-01-01 18:30:00: Rel.:678   : Active:678    M:610    S:66      B:2      D:0      O:0      N:0      Buffer:678      0% step time =  4.8 ms
    C000 83% step 0570:H0019b19-20 Day +00 19:00 2017-01-01 19:30:00: Rel.:698   : Active:698    M:630    S:66      B:2      D:0      O:0      N:0      Buffer:698      0% step time =  4.3 ms
    C000 87% step 0600:H0020b20-21 Day +00 20:00 2017-01-01 20:30:00: Rel.:742   : Active:742    M:678    S:62      B:2      D:0      O:0      N:0      Buffer:742      0% step time =  4.7 ms
    C000 91% step 0630:H0021b21-22 Day +00 21:00 2017-01-01 21:30:00: Rel.:762   : Active:762    M:739    S:13      B:10     D:0      O:0      N:0      Buffer:762      0% step time =  3.9 ms
    C000 96% step 0660:H0022b22-23 Day +00 22:00 2017-01-01 22:30:00: Rel.:805   : Active:805    M:787    S:10      B:8      D:0      O:0      N:0      Buffer:805      0% step time =  4.9 ms
    C000 100% step 0690:H0023b23-00 Day +00 23:00 2017-01-01 23:30:00: Rel.:805   : Active:805    M:793    S:0       B:12     D:0      O:0      N:0      Buffer:805      0% step time =  6.6 ms
    C000 >>> Note: Hydro-model is "3D", in geographic coords = "False"  type "SCHISMreaderNCDF"
    C000       hint: Files found in dir and sub-dirs of "../demos/demo_hindcast/schsim3D"
    C000 >>> Note: When using a terminal velocity, ensure time step is small enough that vertical displacement is a small fraction of the water depth, ie vertical Courant number < 1
    C000 ----------------------------------------------------------------------
    C000   - Finished case number   0,  param_test1 started: 2024-12-12 11:38:27.093392, ended: 2024-12-12 11:39:01.423900
    C000       Computational time =0:00:34.330508
    C000 --- End case 0 -------------------------------------------------------
    End --- Summary ----------------------------------------------------------
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End     >>> Note: to help with debugging, parameters as given by user  are in "user_given_params.json"
    End     >>> Note: Run summary with case file names in "*_runInfo.json"
    End >>> Warning: Deleted contents of existing output dir
    End ----------------------------------------------------------------------
    End ----------------------------------------------------------------------
    End OceanTracker summary:  elapsed time =0:00:35.434000
    End       Cases -   0 errors,   0 warnings,   2 notes, check above
    End       Main  -   0 errors,   1 warnings,   2 notes, check above
    End   Output in c:\Work\ot_install_test\oceantracker\tutorials_how_to\output\param_test1
    End ----------------------------------------------------------------------
    

Options when running at command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These allow

- redefining the input and output dirs given within parameter file,
  which may have been built for a different location
- limiting the run duration or the number of parallel cases during
  testing

the full arguments are below

.. code:: ipython3

    !python ../oceantracker/run_ot_cmd_line.py -h


.. parsed-literal::

    usage: run_ot_cmd_line.py [-h] [--input_dir INPUT_DIR]
                              [--root_output_dir ROOT_OUTPUT_DIR]
                              [--processors PROCESSORS] [--duration DURATION]
                              [--cases CASES] [-debug]
                              param_file
    
    positional arguments:
      param_file            json or yaml file of input parameters
    
    options:
      -h, --help            show this help message and exit
      --input_dir INPUT_DIR
                            overrides dir for hindcast files given in param file
      --root_output_dir ROOT_OUTPUT_DIR
                            overrides root output dir given in param file
      --processors PROCESSORS
                            overrides number of processors in param file
      --duration DURATION   in seconds, overrides model duration in seconds of all
                            of cases, useful in testing
      --cases CASES         only runs first "cases" of the case_list, useful in
                            testing
      -debug                gives better error information, but runs slower, eg
                            checks Numba array bounds
    

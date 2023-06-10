Output files
============

After runnnig ouput files are in the iles are folder given by parameters
.\\“root_output_dir”\\“output_file_base”

The main files are:

-  users_params_*.json, a copy of the parameters as supplied by the user

-  \_runInfo.json holds file names of case files

-  \_caseInfo.json files, have all the output files for each case run
   (only 1 case in this example), plus infomation about the run and data
   useful in plotting

-  \_caseLog_log.txt has a copy of what appeared on the screen during
   the run

-  \_tracks.nc holds the particle tracks in a netcdf file, see below for
   code example on reading the tracks

-  \_grid_outline.json are the boundaries of hydrodynamic model’s domain
   and islands, useful in plotting

-  \_grid.nc a net cdf of the hydo-model’s grid and other infomation,
   useful in plotting and analysis

Below list the files after running the minimmal example.

.. code:: ipython3

    # show a list of output files afte running  mimmal_exampe
    import glob
    for f in glob.glob('.\\output\\minimal_example\\*'):
        print(f) 
    
    


.. parsed-literal::

    .\output\minimal_example\minimal_example_caseInfo.json
    .\output\minimal_example\minimal_example_caseLog_log.txt
    .\output\minimal_example\minimal_example_grid.nc
    .\output\minimal_example\minimal_example_grid_outline.json
    .\output\minimal_example\minimal_example_log.txt
    .\output\minimal_example\minimal_example_runInfo.json
    .\output\minimal_example\minimal_example_tracks.nc
    .\output\minimal_example\users_params_minimal_example.json
    

::


    ---------------------------------------------------------------------------

    NameError                                 Traceback (most recent call last)

    Cell In[1], line 9
          7 import json
          8 with open('A_minimal_example.json','w') as f: 
    ----> 9     json.dump(params, f)
    

    NameError: name 'params' is not defined




.. _running-oceantracker:

#####################
Running OceanTracker
#####################

Ways to run
============================
OceanTracker can be run in two ways.

#. From command line using  json or yaml parameterfile eg.

    ``python run_oceantracker.py --param_file my_params.json``

    or

    ``python run_oceantracker.py --param_file my_params.yaml``

    Then write code to do post processing and/or plotting, using oceantracker.post_processing.* or with user's own tools.

#. From python code in IDE  ( eg PyCharm, Visual Studio) by:

    * creating a parameter dictionary by either:
        * building a parameter dictionary in code, or
        * reading a json or yaml parameter file
    * passing the parameter dictionary  to main.run() method
    * adding optional code for  post processing and/or plotting using oceantracker.post_processing.*

.. note::

    If OceanTracker was installed with a virtual environment, activate it first. Eg. in linux, if in dir above OceanTracker package, then:

    ``source ./oceantracker/venv/bin/activate``

    or windows

    ``conda activate oceantracker``

.. include:: ../demos/minimal_example.rst


Run from parameter file
============================

Using run_oceantracker.py, eg.

``python run_oceantracker.py --param_file YAMLinputFiles\demo01_plot_tracks.yaml --input_dir demohindcast --root_output_dir output\demo01 --duration 3600``

Command line parameters of run_oceantracker.py can override input and output dirs in the parameter file. Usage

.. code-block:: python

    python run_oceantracker.py --param_file  ./demos/demo02_animation.json   ( + options below)

    usage: run_oceantracker.py [-h] [--param_file PARAM_FILE]
                           [--input_dir INPUT_DIR]
                           [--root_output_dir ROOT_OUTPUT_DIR]
                           [--processors PROCESSORS] [--replicates REPLICATES]
                           [--duration DURATION] [--cases CASES] [-debug]

    optional arguments:
      -h, --help            show this help message and exit
      --param_file PARAM_FILE
                            json or yaml file of input parameters
      --input_dir INPUT_DIR
                            overrides dir for hindcast files given in param file
      --root_output_dir ROOT_OUTPUT_DIR
                            overrides root output dir given in param file
      --processors PROCESSORS
                            overrides number of processors in param file
      --replicates REPLICATES
                            overrides number of case replicates given in param
                            file
      --duration DURATION   in seconds, overrides model duration in seconds of all
                            of cases, useful in testing
      --cases CASES         only runs first "cases" of the case_list, useful in
                            testing
      -debug                gives better error information, but runs slower, eg
                            checks Numba array bounds



YAML files
---------------------------

Example of parameters as yaml file , where indenting with spaces (not tabs) creates nested dictionaries.

.. raw:: html

   <details>
   <summary> yaml parameter file </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo55_SCHISM_3D_fall_velocity.yaml
    :caption:
    :language: Yaml

.. raw:: html

   </details>



JSON files
---------------------------

Example   demos\\JSONinputFiles\\demo01_plot_tracks.json

.. raw:: html

   <details>
   <summary> json parameter file </summary>

.. literalinclude:: ../../../demos/demo_json/demo01_plot_tracks.json
    :caption:
    :language: JSON

.. raw:: html

   </details>

Run from code
==============

Below is example of building a dictionary of parameters, running particle tracking and plotting:



Another exmaple

.. literalinclude:: ../../../demos/run_from_code_demo.py
    :caption:
    :language: python




Run from code in python IDE
============================

# Visual Studio

# PyCharm





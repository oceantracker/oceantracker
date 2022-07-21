##########################
Output files
##########################

Output location
=====================


    Output is written to directory given by shared_parameters, ie. a dir named

        ``['root_output_dir']/['output_file_base']``

        eg. ``output/minimal_example``

    **Note:** To make it easier to keep output  from different runs separate, the date  can optionally be added to the dir name
    by setting  shared_params 'add_date_to_run_output_dir' to be  True

File names
=====================

    All files start with the given parameter ['output_file_base'] ie. files have form

        ``['root_output_dir']/['output_file_base']/['output_file_base']*.*``

        eg. ``output/minimal_example/minimal_example*.*``

    If more than one case is run or there are replicate runs requested, files are tagged by case number and replicate number, eg.

        ``output/minimal_example/minimal_example_C010R02*.*``


File types and roles
========================

_runInfo.json
_________________

    Records overall information about the run, such as
        * run start and ends times
        * all output file names used to locate them to read for post processing, eg.
            * the dir which has the output "run_output_dir"
            * name of hindcast grid file netCDF to be used for plotting
            * a list of file names of the _caseInfo.json files, which hold the details of each case
        * copy of user supplied parameters
        * over all performance across all cases
        * ocean tracker version
        * basic info on computer running code

_runLog.txt
_________________

    Has the screen output associated with main.rum(), ie lines starting with "M" on the screen. This covers setup progress, parameter checking, ....


_caseInfo.json
_________________

    Holds useful details about each case run

    * case run start and ends times
    * hindcast details, eg, start end time step, ...
    * all output file names to locate them to read for post processing, eg.
        * the dir which has the output "run_output_dir"
        * name of hindcast grid file netCDF to be used for plotting
        * particle track output files
        * lists of file names of output files from the outputs on each particle_statistics, particle_concentrations, event_loggers etc, add to computational pile line
    * full set of parameters used with all defaults
    * over all timing performance with in some sections of
    * part information
        *  map from namt to numerical values of particle_status_flags which as  recorded in the output
    * basic info on computer running code


_caseLog.txt
_________________

    Has the screen output associated with each individual case, starting with ``P001:`` etc.

_grid.nc
_________________

    The hindcast grid as netCDF file, used for plotting.

_tracks.nc
_________________

    The recorded particle tracks and particle propeties in a netCDF file.


_stats_??_nnn.nc
_________________

    Output as netCDF file, from each class added to list of particle_statistics, nnn is the sequence number as added to list, eg.  ``??_stats_gridded_age_001.nc``

_events_nnn.nc
_________________

    Output as netCDF file, from each class added to list of event_loggers, nnn is the sequence number as added to list, eg.  ``??_events_001.nc``

_concentrations_nnn.nc
_______________________

    Output as netCDF file, from each class added to list of particle_concentrations, nnn is the sequence number as added to list, eg.  ``??_concentrations_001.nc``








# To do List

# Required for version 0.5

1. ~~exit if using obsolete  params~~
2. relese groups
    1.  flag if point or polygon all outside domain, 
    4.  flag if none released ie always dry, 

2.  ~~run and warn of non releasses~~, improve repotring of releases errors at run end
3.  flag error if any end  before start in scheduler
4. try to write partial json if error
5. better way to note release errors, only flag any points that never released at end, or show release success?
1. Stats to work on list of acceptable statuses, not min max?
1. ScishimV5 reader
    1. Bug fix in sigma profile builder for WHOI hindcast
1. DEFT3D FM
   1. 2D reader
   1. 3D sigma reader
   1. Fixed z reader as LSC grid
1. Matlab release group reader
1. Restructure case info 
    1. . ??
1. Nested grids
    1.. ??
1. in case runner create all user requested instances and merge params in one step
1. build check that all classes are initialised and finalized
1. Docs
    1. check all how to note books run, set up code to run all notebooks
    
1. write of case info file even if errors, trap json encoding erorrs 
  

##  Internal Structure

1. Ensure all classes call final setup (core_roles first) 
2. Move all schedulers to final set up
2. add group to make instance.info instead of 'type', to should type be group?
1. Cleaner exiting when error
    1. trace backs
    1. always get secondary case.json info error?
1. move setup dispersion and re-suspension to oceantracker_case_runner
1. Have aperchet check default values in type, range etc as coding errors

### Breaking internal changes
1. convert to part_ops.set_values( part_prop,,.. active) form



## New additions

1. helper method to add to  polygon lists of a class
2. unit tests
    1. write ref case option
    1. master.py to run all tests 
1. check pointing of run to enable restart
1. native global lon-lat  models
1. used np.datetime64, milli sec internally
2. Add positive=True to param checker to enzure vale is >0
1. asarray option to numerical param list checker
    

## Niggles that need sorting some time

1. Message logger ~~tidy up exit if prior error~~
1. better flows in parameter checking crumb trail
    1.??? 
1. Release group is dry some of the time so fails to release, some times and gives , fatal error if none released?
2. readerr grid variable map in base_ reader?
3. tracks eadfer to reain dead particle locations in retangular form
1. isodate time zero param for all readers? apply it outside reader_read_time() method, put as time offsets in hours to merge nested readers?
1. List check makes default values of None into [], should be None? Look at merging list params, better to remove, or keep for building polygon lists ?
1. all final_setup()' s done??
1. inside polygon class over writes given points with closed polygon 
1. cope with time dependent water depth in write to grid
    
## Nice to haves
1. attach name of method to message loggers crumb trail
1.  read polygons with fiona?
1. ~~Write islands to net cdf as packed varaible~~
1. make param keys case insensitive
1. allow starts/ends to be float , sec since 1970, isostr, datetime, np.datetime64, durations to be floats, time delta or np.time delta
1. only put files with output fies claseses in case info output_files

1. cleaner to make write plot function from returned plot?
2. web links to help on error
1. Readers,  get data from function,  to use for gyre test cases
1. tidal constituents reader
1. make al reader inherit from unstructured or structured based class
1. error handling and log file permission errors when reunning cells in note books
1. read write polygons from geo-jsons, release groups poly stats
1. date/time param checker allowing stat end times as double, isostring, datetime , np.datetime64
1. add netcdf variable atributes. dimesions etc when reading output

# Other

## Docs

1. split params into basic and advanced based on capitalized first letter
1. put  class doc str on page

1. Add units to Parameter check and show in user docs
1.  add message logging to post processing
1.   add read case info file with not found errors
        #    add doc string for improtant methods and classes



## checks
1. setup of using AZ profiles from hindcast



##   TUTORIALS
1.   Reader param and adding fields
1.   dispersion resupension

## PERFORMANCE
1.  kernal forms of hori/vert walk
1.   kernal form of water vel interpolator
1.   kernal RK solver
1.    fraction to read use ::10 form to only read load a fraction of track/timestats time steps? can this work in compact filesode?
1.   indepth look at circle test results

#   STRUCTURE
1.    hyperlinks to online docs where useful
1.   much cleaner to  do residence times/stats for all polygon release groups given!
1.   or better get user to define polygons like polygon statistcs, or merge with polygon stats
1.    use update_interval everywhere as parmateter fo periodic actions
1.    revert to index zero for all IDs and data loading
1.   show defauls on param eros?

1.    move particle comparison methods to wrapper methods
1.   full use of initial setup, final set up and update with timers
1.   get rid of used nseq in favour of instanceID
1.   add check for use of known class prop types, eg 'maunal_update'


1. add a convert compact at end if requested


##   IMPROVEMENTS
1.   allow numpy arrays in "array" type
1.   smart way to tell class_dict item does not belong to that type, without class name
1.   allow isostr, datetime, np.dateime64 for dates

1.    rotate particle relese polygns to reduce searches for points in side
1.    extend inside polygon to have list of cells fully inside plogon for faster serach done??
1.    replace retain_culled_part_locations with use of "last known location",
1.   and add "show_dead_particles" option to tracks plotting
1.   plot routines using message logger ???
1.   merge residence time into polygon stats?
1.   add variance calc to on fly stats particle prop, by adding sum of squares heatmap/ploygon
1.    read geojson polygons
1.   free run through statr/gaps/ends when no active particles

1.   add CPC for check dicts of class parameters??
1.  more consisted crumb use for all message logger errors to aid debug
1.   merge demo plots back into demos
1.   particle property, fill value is fill value, not intial, value, put in netcdf, compact reader pyhton and matlab, than fills matrix
1. status to have not released before creataion, dead afet death  in compact reader,
1.  ensures statatus is not released when filling upper left of reytangular matrix
1.   say why no particles found, eg outside domain etc
 
 ##   Simplify


1.   tidy up particle concentrations, add grid data to netcdf

##   FUTURE
1.   Kernal RK steps
1.   aysc reader
1.   FIELD group to manage readers/interp in multi-reader future
1.     move reader opertions to field group mangager to allow for future with multiple readers
1.    attach reader/interp to each  field instance to
1.   support for lat long inout/output
1.    as a utility set up reading geojson/ shapely polygons and show example
1.    grid outline file as geojson?


#   TESTING
    #   test case fall vel no dispersion
1. ~~  reprducable  test cases with random seed to test is working~~

##    ERROR HANDLING
1.   improve crumb trail use in paramters and elsewhere
1.    check in no if main for parralel case, to avoid  error on windows if running in //
1.   case info not found on graceful exit error

##   SIMPLIFY

1. add part property from field wwhich checks if field exists
1.  field type reader, derived from reader field ,  or custom


##   ISSUES
1.     in making custom fields how do i know fiels have been added before i use i
1.    how doi know part prop which depend on others are up to date before use
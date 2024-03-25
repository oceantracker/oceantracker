# To do List

# Required for version 0.5

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
1. build check that all classes are initialised and finalized
1. Docs
    1. ???
    
    
    

##  Internal Structure

1. Ensure all classes call final setup (core_roles first) 
2. Move all schedulers to final set up
2. add group to make instance.info instead of 'type', to should type be group?
1. Cleaner exiting when error
    1. trace backs
    1. always get secondary case.json info error?
 1. move setup dispersion and re-suspension to oceantracker_case_runner


### Breaking internal changes
1. convert to part_ops.set_values( part_prop,,.. active) form



## New additions

1. helper method to add to  polygon lists of a class
2. unit tests
    1. write ref case option
    1. master.py to run all tests 
    

## Niggles that need sorting some time

1. Message logger
    1. tidy up exit if prior error
1. better flows in parameter checking crumb trail
    1.??? 
1. Release group is dry some of the time so fails to release, some times and gives , fatal error if none released?
    
## Nice to haves
1. attach name of method to message loggers crumb trail
1.  read polygons with fiona?

# Docs

1. split params into basic and advanced based on capitalized first letter




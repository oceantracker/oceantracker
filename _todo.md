# To do List

# Required for version 0.5

1. Stats unit test
1. matlab read stats check
2.  fix demo matalb plot axes 
3. split particles writing track   files, are not readable
3. map scale on latlong grid too big
   
1. add descriptions to particle properties to put in netcdf if written out

2. centalize polygon list creation and param checking 
4. ensure error log is written on caught error
1. polygon_list param spell checking 
1. grid stats areas in sq m for geographic coord, check ploygon areas in geographic ( add local grid function for these)
1. grid release slow! test release point is dry not all of pulse, pre test grid points outside domain and disable 
##  Internal Structure

## New additions?

1. helper method to add to  polygon lists of a class
1. check pointing of run to enable restart
1. used np.datetime64  internally 
2. update timer for reader classes

# Niggles that need sorting some time
3. compact tracks writer to retain dead particle locations in retangular form, but flag as dead
1. List check makes default values of None into [], should be None? Look at merging list params, better to remove, or keep for building polygon lists ?
1. cope with time dependent water depth in write to grid
3.  reader grid transforms faster with pre-allocated buffers?
4. unit test 01,  track diff. between LSC and sigma vertical regrid too large?
5. vertical regrid using z fractions for each time step?
6.  adding custom reader fields, reader fields, eg deg_t0_lat_long updating? and part prop updating ordering?
1. max_duration and end time estimates
8. LSC unit test slow?  release stratergies?
9.  speed nested grids, only check if particle on outer grid is inside an inner grid if in a cell overlapping  an inner grid 
1. when converting from meters to latlong grid, need to rotate vel to be north/south, east/west??
## Nice to haves
1.   remove_tidally_stranded_particles option?
1. attach name of method to message loggers crumb trail
1.  read polygons with fiona?
1. make param keys case insensitive?
1. allow starts/ends to be float , sec since 1970, isostr, datetime, np.datetime64, durations to be floats, time delta or np.time delta
1. only put files with output fies classes in case info output_files
1. cleaner to make write plot function from returned plot?
2. web links to help on error
1. Readers,  get data from a function not file,  to use for gyre test cases
1. tidal constituents reader
1. read write polygons from geo-jsons, release groups poly stats
1. add netcdf variable atributes. dimensions etc when reading output
1.  add message logging to postprocessing
2.  remove dimension map in favour of using get_hindcast_info() method
1. make subgrids spaning polygons with own kdtree to speed lookup of initial cell find
2. speed inside polygon by when cell is known, for triangles fully inside a ploygon
3. radius point release separated from point release to do inside domain check at start  
4.  cellsearch status flags as numba compile time constants
1. Grid and point release, only check in inise domain at start and disable releases from these points?
6. move point release with raduuis to sepeate class based on polygon release
5. 
# Other

## Docs

1.   add read case info file with not found errors 
2. add doc string for important methods and classes
1.    hyperlinks to online docs where useful
2. 
##   TUTORIALS
1.   Reader param and adding fields
1.   dispersion resupension

## PERFORMANCE
1.  kernal forms of hori/vert walk
1.   kernal form of water vel interpolator
1.   kernal RK solver
1.   indepth look at circle test results
1. nested grids, make check if indide inner grid faster by flaging outer grid tri overlaping inner grid

#   STRUCTURE

1.   much cleaner to  do residence times/stats for all polygon release groups given!
2.   1. faster to do dry cellby updating adjacency matrix? aviods addtional decsion in cel serach
1. add a convert compact tracks file at end if requested


##   IMPROVEMENTS

1.    rotate particle relese polygns to reduce searches for points in side
1.    replace retain_culled_part_locations with use of "last known location",
1.   plot routines using message logger ???
1.   add variance calc to on fly stats particle prop, by adding sum of squares heatmap/ploygon
1.    read geojson polygons
1.   merge demo plots back into demos
1.  ensures status is not released when filling upper left of reytangular matrix
 
 ##   Simplify
1.   tidy up particle concentrations, add grid data to netcdf

##   FUTURE
1.   aysc reader
1.    attach reader/interp to each  field instance to
1.    add a utility set up reading geojson/ shapely polygons and show example
1.    grid outline file as geojson?


#   TESTING
    #   test case fall vel no dispersion
1. ~~  reprducable  test cases with random seed to test is working~~

##    ERROR HANDLING
1.   improve crumb trail use in paramters and elsewhere
1.   more consisted crumb use for all message logger errors to aid debug
1.    check in no if main for parralel case, to avoid  error on windows if running in //
1.   case info not found on graceful exit error



####################
Features
####################


Main Features
=================

* Ability to calculate tracks of  millions of particles in hours in unstructured grids.
* Reads hydrodynamic model output from Schism, FVCOM, plus support for ROMS structured grid  output.
* Calculate particle statistics one the fly, eliminating need to store and wade though large volumes of particle track output.
* Flexible parameter file driven particle tracking,
* Computational pipeline built fom given parameters, eg. add particle properties, add to modifies particle trajectories, calculates statistics etc,  to the pipe line.
* Flexible particle releases, from multiple points or polygons.
* Forwards and backwards in time particle tracking.
* Run multiple cases in parallel, to reduce run time.
* Post run plotting and animation.
* Flexible python code, with key computational code using Numba, running at C code speeds.


Useful Features
=================

* Numerics

    * Fast native grid particle tracking for both S-layer,plus and Schism's LSC vertical grids
    * Loglayer vertical interpolation of water velocity for particles in bottom layer, giving more realistic behaviour, eg. resuspension.
    * Linear horizontal interpolation within triangles, and depth cell except for velocity in bottom cell.

* Particle behaviour
    * Resuspension from the bottom based on critical friction velocity.
    * Shoreline stranding/re-floating of particles by the tide based on dry cells.
    * "InPolygon" particle property which notes which of a set of polygons they lies within. Useful for polygon based statistics and changing behaviour inside polygons.

* Particle release
    * add multiple "release_groups", particles release at same locations and times
    * set different release time, dates, duration for release, plus maximum age.
    * choose whether to release particles in cells which are dry due to the tide
    * release depth can be random within water column, or given depth range.
    * random release with arbitrary polygons, in areas which dont overlap land.


* Computational-pipeline abstraction
    * Abstracts the details of working with vectors, 2D or 3D variables away from user
    * add multiple velocity modifiers, trajectory modifiers to the pipeline
    * dead particles culled from computation and particle buffers, speeding run, eg. those older than given maximum age.


* Output
    * netCDF files, with json files containing other useful information
    * calculation of on-the-fly statistics as gridded heat maps or polygon connectivity writen to netcdf. Separate statistics for each release group.
    * track plotting and animation code
    * events class output, which only writes output when events occur, eg. a particle entering or exiting given polygons

* Internal automation
    * Automatically interpolates user fields named by the user to the particle locations, and writes this particle property to the output file.
    * Splits quad cells into triangles on the fly
    * automates management of particle property buffers, expanding as more are released, culling from computation when there are significant numbers of dead particles
    * Reads netcdf hydrodynamic model output detecting format at automatically determining whether 2D or 3D
    * Flexible reader with user configurable mapping  file variable names to consistent internal variable names.
    * Sorts all hindcast files found in a dir and its sub-dirs into time order, based on time variable in the file. Avoiding need to use file name structure to load files in date order.
    * Internal buffers for particle properties automatically expand as more particles are released needed.

Architecture
===============

* Fully driven by parameters in JSON/YAML file or in code from dictionary
* Highly flexible architecture enabling:
    * user implemented approaches to core classes, core classes can be replaced via string name in parameter dictionary, eg. user spatial interpolator
    * adding user developed:
        * custom particle properties derived from other properties though inheritance
        * augment particle velocity given by water_velocity read from hindcast, eg. particle fall velocity
        * modify particle trajectories, eg. resuspension.

* Automated processes to add user developed particle proprieties, velocity, trajectory modifiers, etc , to calculation and output chain. Eg  Requesting a file variable "temperature" from hindcast file by adding to the readers "field_variables" list, will automatically:
    * create a feild of this name
    * interpolate this field to the particle locations at each time step
    * write this particle property to the output file along with the particle location etc.

* All core and optional classes can be changed or added to list as parameter string using class_name as a string, eg optional particle distance travelled property.
* Reduce memory requirement in 'compact_mode',  which only retains active particles, eg. those young enough to be of interest.
* Written in python with numba package for fast in-place operations on particle properties and hindcast's fields based on set of indices arrays.

















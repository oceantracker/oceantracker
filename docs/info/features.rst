####################
Features
####################


Main Features
=============

* Ability to calculate tracks large amount of particles in unstructured grids. E.g. it takes about 4 hours to simulate the the trajectory of one million particles for one year.
* Large set of natively supported hydrodynamical models (see XX)
* Calculate particle statistics on the fly, eliminating need to store and wade though large volumes of particle track output.
* Flexible parameter file driven particle tracking,
* Computational pipeline built fom given parameters, eg. add particle properties, add to modifies particle trajectories, calculates statistics etc,  to the pipe line.
* Forwards and backwards in time particle tracking.
* Post run plotting and animation.
* Flexible python code, which uses Numba for to speed up computationally expensive code to C-like speeds.

Supported hydrodynamical models
===============================
The following table shows the currently supported hydrodynamical models.
Feel free to reach out if your model isn't on the list. 
Reads hydrodynamic model output from Schism, FVCOM, plus support for ROMS structured grid  output.

.. list-table::
   :header-rows: 1
   :widths: 20 30 15 15 15

   * - Hydrodynamic model name
     - Description
     - Horizontal grid type
     - Horizontal coordinates
     - Vertical grid type
   * - SCHISM (Semi-implicit Cross-scale Hydroscience Integrated System Model)
     - Schism is a multi-scale, multi-physics hydrodynamic model for simulating flows in the atmosphere, ocean, and coastal regions (Zhang et al., 2016).
     - Unstructured triangular mesh.
     - Geographic and Cartesian
     - S-layer and LSC vertical grids.
   * - Finite Volume Community Ocean Model (FVCOM)
     - FVCOM is a prognostic, unstructured-grid, finite-volume, free-surface, 3D primitive equation coastal ocean circulation model (Chen et al 2003).
     - Unstructured triangular mesh.
     - Geographic and Cartesian
     - Sigma (terrain-following) vertical coordinates.
   * - The Regional Ocean Modelling System (ROMS)
     - ROMS is a free-surface, terrain-following, primitive equations ocean model widely used by the scientific community for a diverse range of applications (e.g., Haidvogel et al., 2000).
     - Arakawa C-grid (rectilinear and curvilinear)
     - Geographic
     - Sigma (terrain-following) vertical coordinates.
   * - CMEMS catalogue
     - CMEMS public catalogue for near real time and reanalysis products. Entry covers products provided on a standard Arakawa A-grid and adhering to community standards.
     - Arakawa A-grid (rectilinear and curvilinear)
     - Geographic
     - Z-level (fixed depth) vertical coordinates.
   * - Delft3D
     - Delft3D is a modelling suite for hydrodynamics, waves and sediment transport. Classic Delft3D-FLOW uses curvilinear structured grids; Delft3D Flexible Mesh (FM) uses unstructured triangular meshes.
     - Curvilinear structured or unstructured triangular mesh (implementation dependent)
     - Geographic
     - Sigma (terrain-following) or z-level depending on implementation.

Useful Features
===============

* Numerics

    * Linear horizontal interpolation within triangles, and linear vertical interpolation except for velocities in the bottom cell.
    * Loglayer vertical interpolation of water velocity for particles in bottom layer, giving more realistic behaviour, eg. resuspension.
    * 'hotstart' for restarting interupted runs 

* Particle behaviour
    * Settling on the bottom, with resuspension based on critical friction velocity.
    * Tidal stranding and resuspension of particles by on model dry cells.
    * Vertical velocities 
    * "InPolygon" particle property which notes which of a set of polygons they lies within. Useful for polygon based statistics and changing behaviour inside polygons.
    * Split particles, to give two child particles at given frequency and probability

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

* Other
    * If no particles active, will freerun until some are released, allows particles to be released for one season per year, with a max age, and run will skip between years

















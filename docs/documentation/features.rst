Features
====================


.. * Read and visualize model output quickly with .
For an overview see :doc:`feature overview </overview/features.rst>`.
For more detailed descriptions about individual features see below:

.. toctree::
   :maxdepth: 2

   features/readers.rst
   features/vertical_grids.rst
   features/supported_models.rst
   features/computational_speed.rst
   features/computational_pipeline.rst
   features/integration_methods.rst
   features/interpolation.rst
   features/particle_properties.rst
   features/trajectory_modifiers.rst
   features/statistics.rst
   features/restart_continue.rst

.. * General
..     * Forwards and backwards in time particle tracking.

.. * Particle behaviour
..     * Settling on the bottom (with resuspension based on critical friction velocity).
..     * Tidal stranding and resuspension (of particles by on water level or model dry cells information).
..     * Vertical velocities 
..     * "InPolygon" particle property which notes which of a set of polygons they lies within. Useful for polygon based statistics and changing behaviour inside polygons.
..     * Split particles, to give two child particles at given frequency and probability

.. * Particle release
..     * add multiple "release_groups", particles release at same locations and times
..     * set different release time, dates, duration for release, plus maximum age.
..     * release depth can be random within water column, or given depth range.
..     * random release with arbitrary polygons.

.. * Output
..     * Model output is proveided as netCDF files, with json files containing information about the model run.


.. * Numerics

..     * 'hotstart' for restarting interupted runs 

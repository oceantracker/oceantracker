Interpolation
-------------

Linear **horizontal** interpolation
    All model grids are handled as triangular fields. 
    Fields that are not triangular, e.g. rectangular or mixed fields split all non triangular cells into triangles.
    These triangles are then interpolated using 2-dimensional `barycentric coordinates <https://en.wikipedia.org/wiki/Barycentric_coordinate_system>`_.

Linear **vertical** interpolation except for velocities in the bottom cell.
**Bottom cells** use log-layer interpolation in the vertical for the water velocity for particles in bottom layer.
###############################
Vertical grid types and support
###############################

Different oceanographic models use different vertical grids.
The trade of - if they weren't chose for historic reason - are typically between computational efficiently and accuracy.
The most common grid types are, in order of increasing complexity, z-level, sigma, s-layer, and LSC.

Description of the vertical grid types supported in oceantracker
================================================================


z-level grids
-------------

A z-level grid uses fixed-depth (geopotential) levels that are horizontal everywhere, independent of bathymetry.
Layer interfaces are at constant depth, i.e. z values (e.g., 0 m, 10 m, 20 m)
Hence, the bathymetry is represented by "steps" with "partial bottom cells" where the sea floor cuts through the lowest layer.
This simplicity makes them computationally fast, and reasonably accurate in large-scale open ocean model with relatively smooth bathymetric.
In more steeply - relative to the horizontal resolution - varying coastal regions, however, the "staircase representation" of the bottom can lead to inaccuracies in bottom boundary layer processes.

.. figure:: https://www.oc.nps.edu/nom/modeling/images/z_coords.jpg
    :alt: Z-level grid diagram

    Example of a z-level grid structure.
    Source: https://www.oc.nps.edu/nom/modeling/vertical_grids.html

Note, that the z-level system has some variance.
Some allow a free-surface, while other not-only allow a free surface but internally - i.e. generally not within the model output - rescale the vertical levels to follow the free surface.
The latter is often referred to as a z*-vertical-grid

.. figure:: https://www.nemo-ocean.eu/doc/img210.png
    :alt: Z-level variance grid diagram

    (a) z-coordinate in linear free-surface case; (b) z-coordinate in non-linear free surface case; (c) re-scaled height coordinate (become popular as the z*-coordinate [Adcroft and Campin, 2004]).
    Source: https://www.nemo-ocean.eu/doc/node9.html



Sigma (terrain-following) grids
-------------------------------

A sigma grid improves on the "staircase representation" by being terrain-following.
The vertical coordinate sigma (:unicode:`U+03C3`)is scaled by total local depth, i.e. water depth is represented as a fraction of total depth at that location.
Another way of saying this is that the sigma layers follow the shape of the terrain.
Therefore model layers conform to the sea surface and bottom at every horizontal location.
In shallow areas, physical layer thickness is small, while in deep regions the same :unicode:`U+03C3` interval corresponds to a thicker layer, 
but every column retains the same set of :unicode:`U+03C3` levels.
Due to the fixed vertical fraction sigma layers tend to struggle with bathymetries where the model needs to represent strongly varying depth levels.
There they may under-resolve deep regions while over-resolving shallow regions.


.. figure:: https://www.oc.nps.edu/nom/modeling/images/sigma_coords.gif
    :alt: Sigma grid diagram

    Example of a sigma grid structure.
    Source: https://www.oc.nps.edu/nom/modeling/vertical_grids.html


s-layer (generalized terrain-following) grids
--------------------------------------------

An s-layer type grid generalizes the classic sigma system by allowing more flexible analytic stretching in the vertical.
The vertical coordinate variable s is a function designed so that layers can behave more like z-levels near the surface in deep water,
while remaining terrain-following near the bottom, and quasi-sigma in shallow regions.
Additionally s-layer vertical grids use spatially varying depth fractions.

For more details see https://www.nemo-ocean.eu/doc/node9.html



LSC (Localized Sigma Coordinates) grids
--------------------------------------

LSC (Localized Sigma Coordinates) is the newest addition to the set of vertical grids.
It was designed for an unstructured-grid called SCHISM.
The key difference from an s-layer is that LSC allows for varying vertical depth layers. 
I.e. in shallow waters it might only use 5 vertical layers while deeper water might be represented with 40 layers.
This introduces "degenerate cells" that are triangular (on xz projections) rather then rectangular.
By reducing the number of cells in shallow regions, this approach allows for a reduction in computational load, especially in coastal and estuarine environments.

.. figure:: https://www.researchgate.net/profile/Chin-Wu-6/publication/268750779/figure/fig3/AS:357090615939074@1462148446261/Comparison-of-vertical-grids-along-the-transect-shown-in-Fig-1-using-a-LSC-2-with_W640.jpg
    :alt: LSC grid diagram

    Vizualisation of an LSC grid Layout from Zhang et al. (2014)
    Source: doi.org/10.1016/j.ocemod.2014.10.003



Overview table
==============

.. list-table:: Overview of vertical grid features
   :header-rows: 1

   * - Grid type
     - varying depth levels
     - varying depth fractions
     - varying number of layers
   * - z-level
     - no
     - no
     - no
   * - sigma
     - yes
     - no
     - no
   * - s-layer
     - yes
     - yes
     - no
   * - LSC
     - yes
     - yes
     - yes
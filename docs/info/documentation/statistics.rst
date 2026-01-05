==============================
On-the-fly particle statistics
==============================

When we run large simulations with billions of particles, recording the their trajectories with a decent temporal resolution quickly becomes unfeasable as file sizes become unmanagably large (>terra bytes).
To avoid this we offer two build-in "on-the-fly" statistics that are produced during the model runtime.
There are currently two types of statistics implemented; time-based and age-based statistics.
Time-based statistics record the spacial distribution of particles (and their spatially averaged "properties", e.g. temperature) at moments in time (e.g. 1am, 2am, etc).
Age-based statistics record the spacial distribution of particles for particles of a certain age (e.g. 1 hours, 2 hours, etc).
The latter is particularly useful when a continuous release of particles is chosen to e.g. calculate a seasonally averaged connectivty between two water bodies.
Both time- and age-based statistics can be calculated either on a horizontal rectangular grid, or for a set of polygons.
They can also be recorded either as 3D or 2D (depth-averaged) statistics.

Time-based statistics
---------------------


Age-based statistics
--------------------


Grid-based statistics
---------------------


Polygon-based statistics



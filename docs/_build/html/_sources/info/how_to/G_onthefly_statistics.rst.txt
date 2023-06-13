On-the-fly statistics
=====================

[This note-book is in oceantracker/tutorials_how_to/]

Scaling up particle numbers to millions will create large volumes of
particle track data. Storing and analyzing these tracks is slow and
rapidly becomes overwhelming. For example, building a heat map from a
terabyte of particle tracks after a run has completed. Ocean tracker can
build some particle statistics on the fly, without recording any
particle tracks. This results in more manageable data volumes and
analysis.

On-the-fly statistics recorded particle counts separately for each
release group. It is also possible to subset the counts, ie only count
particles which are stranded by the tide by designating a range of
particle status values to count. Or, only count particles in a given
vertical “z” range. Users can add multiple statistics, all calculated in
from the same particles during the run. Eg. could add a particle
statistic for each status type, for different depth ranges.

Statistics can be read, plotted or animated with OceanTrackers
post-processing code, see below

The available “particle_statistics” classes with their individual
settings are at …. add link

Currently there are two main classes of particle statistics, “gridded”
and “polygon”.

Gridded statistics
------------------

These are heat maps of counts binned into cells of a regular grid. Along
with heat maps of particle counts, users can optionally build a heat
maps of named particle properties, eg. the value decaying particle
property. To ensure the heat map grids are not too large or too coarse,
by default grids are centred on each release group, thus there are
different grid locations for each release group.

Polygon statistics
------------------

These particle counts can be used to calculate the connectivity between
each release group and a user given list of “statistics” polygons. Also,
used to estimate the influence of each release group on a particle
property with each given statistics polygon. The statistics polygons are
not the same as those used in a polygon release (they can be if the user
requires it). Polygon statistics show effect of each point or polygon
release, on the given statistics polygons. A special case of a polygon
statistic, is the “residence_time” class, which can be used to calculate
the fraction of particles from each release group remaining within each
statistics polygon at each ‘update_interval’ as one way to estimate
particle residence time for each release group.

Particle property statistics
----------------------------

Both types of statistics can also record sums of user designated
particle properties within each given grid cell or statistics polygon,
which originate from each release group. These sums enabling mean values
of designated particle properties within each grid cell or polygon to be
calculated. They can also be used to estimate the relative influence of
each release group on the value of a particle property within each given
grid cell or polygon.

A future version with allow estimating the variance of the designated
property values and particle counts in each grid cell or polygon, for
each release group.

Time verses Age statistics
--------------------------

Both gridded and polygon statistics come in two types, “time” and “age”.

-  “time” statistics are time series, or snapshots, of particle numbers
   and particle properties at a time interval given by
   “calculation_interval” parameter. Eg. gridded stats showing how the
   heat map of a source’s plume evolves over time.

-  “age” statistics are particle counts and properties binned by
   particle age. The result are age based histograms of counts or
   particle proprieties. This is useful to give numbers in each age band
   arriving at a given grid cell or polygon, from each release group.
   Eg. counting how many larvae are old enough to settle in a polygon or
   grid cell from each potential source location.

Gridded example
---------------

::

   # add gridded stats example with plotting

Polygon example
---------------

::

   # add polygon stats example with plotting

Residence time statistic
------------------------

::

   # add example

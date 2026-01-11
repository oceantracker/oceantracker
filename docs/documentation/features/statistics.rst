On-the-fly particle statistics
==============================

When running large simulations with billions of particles, recording the their trajectories with a sufficient temporal resolution
quickly becomes unfeasible as file sizes become unmanageably large (>terra bytes).
To avoid this problem we offer "on-the-fly" statistics that are produced during the model runtime.
Writing statistics during the runtime also drastically reduces the time needed of reading the model output (i.e. trajectories) after the run for analysis,
which in some situations might take just as long as the running the model. 
There are currently two types of statistics implemented; time-based and age-based statistics.
Time-based statistics record the spacial distribution of particles (and their spatially averaged "properties", e.g. temperature) at moments in time (e.g. 1am, 2am, etc).
Age-based statistics record the spacial distribution of particles for particles of a certain age (e.g. 1 hours, 2 hours, etc).
The latter is particularly useful when a continuous release of particles is chosen to e.g. calculate a seasonally averaged connectivity between two water bodies.
Both time- and age-based statistics can be calculated either on a rectangular horizontal grid, or for a set of polygons.
They can also be recorded either as 3D or 2D (depth-averaged) statistics.
Each statistic that you add to the model configuration will produce one netCDF file in the output directory,
that you can either open with you own script or use oceantrackers output loading functions. 

Overview of types of particle statistics
----------------------------------------

Time-based statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For time based stats, particle presence within a grid cell or polygon is checked at fixed time intervals ("update_interval").
The total number of particles within that cell at that moment in time is then written into that corresponding statistics file.
Note however, that this does not guarantee that all particles that pass thru that cell/polygon are counted as they might have passed thru in between update intervals or even within a single time step.
There is one variant of the time-based statistic (currently only implemented for gridded stats) that help avoiding that problem by offering two distinct intervals, one for "updating" i.e. checking if a particle is within a cell and one for writing.
Particle counts are accumulated within the "write_interval".
This allows for much higher update_intervals without increases data volume.
Note, that this may count particles multiple times.
Additionally, particle counts are also distinguishing between particle release location.

The user can also impose a set of constraints to which particles should be counted.
These are status (e.g. settled on bottom), water column depth, particle depth (e.g. only within 10 meters of the surface).
For details see the `API reference`_ or the formal description below.


Age-based statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Age-based statistics work similar time-based ones - i.e. particle presence within a grid cell or polygon is recoreded for each release location - but instead of recording it at fixed time interval we bin particles into age classes.
E.g. you might calculate an yearly averaged connectivity from a source volume by continuously releasing particles from that volume.
Binning these particles by age now allows you to visualize e.g. the dispersion clouds after 1 month.
There is one important caveat to this.
If your update interval is larger then your age bin size (which is recommended for most applications) you will potentially "double count" particles.
E.g. if a particle remains within the same grid cell between update intervals it will be counted in that cell twice.
If it moves to another cell it will be counted once in the first,  and then again in the second.

Grid-based or polygon-based statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Statics can be recorded either on a rectangular longitude-latitude aligned grid
or within a set user-defined polygons.
The grid may either be at a fixed location, or centered on each release groups.
See :doc:`parameter references </documentation/api_ref>` or the `how-to's </getting_started/how_to>` for examples.


Formal descriptions
----------------------------------------

Implementation Notes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The age-based counting approach differs from time-based counting in several important ways:


Gridded Statistics 2D Time-Based: 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``GriddedStats2D_timeBased`` class computes time-series counts of particles within cells of a regular horizontal 2D grid.
At each time step, particles are first filtered based on status criteria, water depth constraints, and vertical position requirements, then binned into spatial grid cells based on their horizontal coordinates.

The count in grid cell :math:`(i,j)` for release group :math:`g` at time :math:`t` is given by:

.. math::

   c_{t,g,i,j} = \sum_{n \in \mathcal{P}_{\text{sel}}(t)} \mathbb{1}_{\{n \in \text{R}_g\}} \cdot \mathbb{1}_{\{(x_n, y_n) \in \text{Cell}_{i,j}\}}

where:

* :math:`c_{g,i,j}(t)` is the count in cell :math:`(i,j)` for release group :math:`g` at time :math:`t`
* :math:`\mathcal{P}_{\text{sel}}(t)` is the set of selected particles at time :math:`t` satisfying the selection criteria
* :math:`\text{R}_g` denotes particles belonging to release group :math:`g`
* :math:`\mathbb{1}_{\{\cdot\}}` is the indicator function returning 1 if the condition is true, 0 otherwise
* :math:`\text{Cell}_{i,j}` is the spatial region defined by the grid cell boundaries

Gridded Statistics 2D Age-Based: 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``GriddedStats2D_ageBased`` class computes age-binned histograms of particle counts within cells of a regular 2D grid.
Unlike the time-based variant, this class accumulates counts across the entire simulation run (or specified time window), binning particles by their age rather than tracking time series.
This approach is particularly useful to calculate water body connectivity or for analyzing age-structured populations, such as tracking different larval age classes in marine ecosystems.

The count in grid cell :math:`(i,j)` for release group :math:`g` in age bin :math:`a` is given by:

.. math::

   c_{a,g,i,j} = \sum_{t \in \mathcal{T}} \sum_{n \in \mathcal{P}_{\text{sel}}(t)} \mathbb{1}_{\{n \in \text{R}_g\}} \cdot \mathbb{1}_{\{(x_n(t), y_n(t)) \in \text{Cell}_{i,j}\}} \cdot \mathbb{1}_{\{\text{age}_n(t) \in \text{B}_a\}}

where:

* :math:`c_{a,g,i,j}` is the accumulated count in cell :math:`(i,j)` for release group :math:`g` in age bin :math:`a`
* :math:`\mathcal{T}` is the set of all update times during the simulation
* :math:`\mathcal{P}_{\text{sel}}(t)` is the set of selected particles at time :math:`t` satisfying the selection criteria
* :math:`\text{R}_g` denotes particles belonging to release group :math:`g`
* :math:`\mathbb{1}_{\{\cdot\}}` is the indicator function returning 1 if the condition is true, 0 otherwise
* :math:`\text{Cell}_{i,j}` is the spatial region defined by the grid cell boundaries
* :math:`\text{B}_a` is the age bin (i.e. range) for bin :math:`a`
* :math:`x_n(t)` and :math:`y_n(t)` are the particle position at time :math:`t`
* :math:`\text{age}_n(t)` is the particle age at time :math:`t`

Polygon Statistics 2D Age-Based
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``PolygonStats2D_ageBased`` class computes age-binned histograms of particle counts within user-defined 2D polygons.
This class accumulates counts across the entire simulation run (or specified time window), binning particles by their age.
This is particularly useful for analyzing age-structured connectivity between geographic regions, such as larval dispersal patterns between marine habitats at different developmental stages.

The count in polygon :math:`p` for release group :math:`g` in age bin :math:`a` is given by:

.. math::

   c_{a,g,p} = \sum_{t \in \mathcal{T}} \sum_{n \in \mathcal{P}_{\text{sel}}(t)} \mathbb{1}_{\{n \in \text{R}_g\}} \cdot \mathbb{1}_{\{(x_n(t), y_n(t)) \in \text{Polygon}_p\}} \cdot \mathbb{1}_{\{\text{age}_n(t) \in \text{B}_a\}}

where:

* :math:`c_{a,g,p}` is the accumulated count in polygon :math:`p` for release group :math:`g` in age bin :math:`a`
* :math:`\mathcal{T}` is the set of all update times during the simulation
* :math:`\mathcal{P}_{\text{sel}}(t)` is the set of selected particles at time :math:`t` satisfying the selection criteria
* :math:`\text{R}_g` denotes particles belonging to release group :math:`g`
* :math:`\mathbb{1}_{\{\cdot\}}` is the indicator function returning 1 if the condition is true, 0 otherwise
* :math:`\text{Polygon}_p` is the spatial region defined by the vertices of polygon :math:`p`
* :math:`\text{B}_a` is the age bin (i.e. range) for bin :math:`a`
* :math:`x_n(t)` and :math:`y_n(t)` are the particle position at time :math:`t`
* :math:`\text{age}_n(t)` is the particle age at time :math:`t`



Particle Selection Criteria
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The selected particle set :math:`\mathcal{P}_{\text{sel}}(t)` consists of particles satisfying:

.. math::

   \mathcal{P}_{\text{sel}}(t) = \{n : s_n \in \mathcal{S}_{\text{allowed}} \land d_{\min} \leq D_n \leq d_{\max} \land \Phi(n)\}

where:

* :math:`s_n` is the particle status (e.g., stationary, moving, on_bottom, stranded_by_tide)
* :math:`\mathcal{S}_{\text{allowed}}` is the set of allowed status values specified in ``status_list`` parameter
* :math:`D_n` is the water depth at particle location
* :math:`d_{\min}` and :math:`d_{\max}` are the water depth constraints (``water_depth_min`` and ``water_depth_max``)
* :math:`\Phi(n)` is the vertical position criterion, defined as:

.. math::

   \Phi(n) = 
   \begin{cases}
   \text{true} & \text{if no depth selection is specified} \\
   z_{\min} \leq z_n \leq z_{\max} & \text{if z-range selection is used} \\
   z_n \leq -D_n + \delta z_{\text{bed}} & \text{if near-seabed selection is used} \\
   z_n \geq \eta_n - \delta z_{\text{surf}} & \text{if near-surface selection is used}
   \end{cases}

where :math:`z_n` is the vertical position of particle :math:`n`, :math:`\eta_n` is the tidal elevation, :math:`\delta z_{\text{bed}}` is the near-seabed distance threshold (``near_seabed`` parameter), and :math:`\delta z_{\text{surf}}` is the near-surface distance threshold (``near_seasurface`` parameter).


Age Bin Definition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A particle with age :math:`\text{age}_n(t)` belongs to age bin :math:`a` if:

.. math::

   \text{B}_a = \{\text{age} : A_{\text{edge}}[a] \leq \text{age} < A_{\text{edge}}[a+1]\}

The age bin edges are uniformly spaced:

.. math::

   A_{\text{edge}} = d \cdot \text{sign}(\Delta t) \cdot \left[\text{age}_{\min}, \text{age}_{\min} + \Delta A, \text{age}_{\min} + 2\Delta A, \ldots, \text{age}_{\max}\right]

where:

* :math:`\text{age}_{\min}` is the minimum age to bin (``min_age_to_bin`` parameter)
* :math:`\text{age}_{\max}` is the maximum age to bin (``max_age_to_bin`` parameter)
* :math:`\Delta A` is the age bin size (``age_bin_size`` parameter)
* :math:`d = +1` for forward tracking, :math:`d = -1` for backtracking
* :math:`\text{sign}(\Delta t)` is the model direction (forward or backward in time)

The age bin index is computed as:

.. math::

   a = \left\lfloor \frac{\text{age}_n(t) - A_{\text{edge}}[0]}{\Delta A} \right\rfloor

Only particles with :math:`0 \leq a < N_{\text{bins}}` are counted, where :math:`N_{\text{bins}}` is the total number of age bins.


Grid Cell Definition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A particle at position :math:`(x_n, y_n)` belongs to cell :math:`(i,j)` if its coordinates fall within the cell boundaries:

.. math::

   \text{Cell}_{i,j} = \{(x,y) : x_{\text{edge}}[g,i] \leq x < x_{\text{edge}}[g,i+1] \text{ and } y_{\text{edge}}[g,j] \leq y < y_{\text{edge}}[g,j+1]\}

The cell indices are computed using floor division:

.. math::

   i = \left\lfloor \frac{x_n - x_{\text{edge}}[g,0]}{\Delta x} \right\rfloor, \quad 
   j = \left\lfloor \frac{y_n - y_{\text{edge}}[g,0]}{\Delta y} \right\rfloor

where :math:`\Delta x` and :math:`\Delta y` are the uniform grid spacings in the x and y directions, respectively.
Note that when ``release_group_centered_grids=True``, the grid edges :math:`x_{\text{edge}}[g,:]` and :math:`y_{\text{edge}}[g,:]` differ for each release group :math:`g`, as each grid is centered on its respective release group's centroid.


Polygon Membership
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A particle at position :math:`(x_n, y_n)` belongs to polygon :math:`p` if:

.. math::

   (x_n, y_n) \in \text{Polygon}_p \Leftrightarrow I_n^{\text{poly}} = p

where :math:`I_n^{\text{poly}}` is the polygon index assigned by the ``InsidePolygonsNonOverlapping2D`` particle property:

.. math::

   I_n^{\text{poly}} = 
   \begin{cases}
   p & \text{if particle } n \text{ is inside polygon } p \\
   -1 & \text{if particle } n \text{ is inside no polygon}
   \end{cases}

Particles with :math:`I_n^{\text{poly}} = -1` are not counted in any polygon.


Connectivity Matrix
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The age-based statistics also compute a connectivity :math:`\mathcal{C}_{a,g,i,j}`,
which represents the probability that a released particle from release group :math:`g` reaches a given grid cell :math:`(i,j)` at a given age :math:`a`.

.. math::

   \mathcal{C}_{a,g,i,j} = \frac{c_{a,g,i,j}}{N_{a,g}^{\text{released}}}

where:

* :math:`C_{a,g,i,j}` is the particle count
* :math:`N_{a,g}^{\text{released}}` is the total number of particles released from group :math:`g` that existed at age :math:`a`

The released particle count in age bins is computed by age-binning the total releases at each counting time:

.. math::

   N_{a,g}^{\text{released}} = \sum_{t \in \mathcal{T}} \mathbb{1}_{\{\text{age}(t) \in \text{B}_a\}} \cdot N_g^{\text{released}}(t)

where :math:`N_g^{\text{released}}(t)` is the cumulative number of particles released from group :math:`g` up to time :math:`t`, and :math:`\text{age}(t) = t - t_0` is the time elapsed since the start of counting.


Note, that the connectivity matrix includes particles that died or exited the domain.
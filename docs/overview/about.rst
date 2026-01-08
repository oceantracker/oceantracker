#############
About
#############

Overview
--------

OceanTracker is a Lagrangian particle tracking model.
Lagrangian particle tracking models calculate the trajectories of particles as they are advected and diffused by ocean currents.
These trajectories can then be used to quantify bio-physical transports in the ocean.

The Lagrangian trajectory approach is in many regards similar to the Eulerian tracer approach, but they also have many differences.
They both represent parcels of water being advected passively by the velocity fields of the,
This makes it possible to trace water masses, substances such as pollutants, or organisms as they are carried with the ocean currents.
A key difference between the approaches is that the Eulerian tracer equation generally needs to be integrated 'on-line' - i.e. at the same time as the hydrodynamics are calculated -
While the Lagrangian trajectories can also be calculated "off-line", after the fact, using the hydrodynamic model outputs.
The 'off-line' calculation of Lagrangian trajectories is far more rapid, as they can leverage the already simulated velocity fields in order to calculate the trajectories.
This enables a large range of studies that would be unfeasible with a tracer-based approach.

While Lagrangian models have been comparatively well established for larger, but coarse, ocean or earth-system models based on structured, i.e. rectangular, grids,
they were at the time when OceanTracker was started relatively underdeveloped for the models using unstructured grids that are frequently used in coastal oceans.
The existing models that were able to calculate trajectories based on data from unstructured grid models were slow due to several technical reasons.
One of these reasons was that, with the standard approaches at the time (binary-trees), finding the current cell of a particle is computationally much more expensive than the same task in a structured grid.

OceanTracker was created to overcome this, and its first version was, at the time, 100s of times faster than its other existing, freely available particle tracker:
when using unstructured grids. 
More significantly, OceanTracker computational speed is similar to that achieved when particle tracking on a regular grid:
(`Vennell et. al. (2021) <https://link.springer.com/article/10.1007/s10236-020-01436-7>`_).
This makes it possible to routinely calculate the trajectories of millions of particles.
A large number of particles allows for much better estimates of dispersion and transport statistics, 
Particularly when the probability of connection is low but the consequences are significant, e.g. the spread of invasive species.
It also enables wider exploration of parameter sensitivity and particles' bio-physical behaviours, to provide robust results.

Why is OceanTracker fast
------------------------

In its current state (2025), OceanTracker is the fastest openly available particle tracker to our knowledge (`Vennell et al. (2025) <https://eartharxiv.org/repository/view/8387/>`_).
Yet, comparing different particle tracking models fairly remains difficult, as there is no standardized feature set and each model tends to be tailored to a slightly different use case.

While computational speed was a key design goal of OceanTracker, compromises where made between speed, steepness of the adoption curve, adaptability  and  the  complexity of its implementation code.
For this we heavily relied on `numba <https://numba.pydata.org/>`_.
Numba is a just-in-time compiler for Python that translates performance critical pieces of code into optimized machine code at runtime.
This allows OceanTracker to be computationally efficient while remaining much more adaptable then if we would have relied on e.g. NumPy,
where we would have had to rely on predefined vectorized implementations for performance critical code.

For an overview of its features, see :doc:`features` or take a look at some examples in the :doc:`gallery`.



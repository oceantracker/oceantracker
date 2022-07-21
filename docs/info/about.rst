
#############
About
#############

Background
===============

Lagrangian particle tracking, is an important tool in quantifying bio-physical transports in the ocean.
Particle tracking in the unstructured grids typically used in coastal regions is computationally slow,
limiting the number of particles and ranges of behaviours that can be modeled.

OceanTracker was created to be 100s of times faster than an existing freely available particle tracker
when using unstructured grids. More significantly, OceanTracker computational speed is simmilar to that achieved when particle tracking on a regular grid
(`Vennell et. al. <https://link.springer.com/article/10.1007/s10236-020-01436-7/>`_)

This makes it possible to routinely calculate the trajectories of millions of particles.
Allowing  large number of particles allows much better estimates of dispersion and transport statistics, particularly when the probability of connection is low but the consequences are significant, e.g. the spread of invasive species.
It also enables wider exploration of parameter sensitivity and particles’ bio-physical behaviours to provide more robust results.

The speed increases result largely from exploiting history and reuse within the spatial interpolation of the hydrodynamic model’s output.
Using multiple computer cores further increased the speed to track a given number of particles.

The code can build heat maps on the fly and within polygon counts. This eliminates the need to record large data sets of particle tracks for post processing into heat maps. In addition to speed the internal architecture of OceanTracker makes it easy for the user to customise and extend.


Architecture
===============

* Fully driven by parameters in JSON/YAML file or in code from dictionary
* Highly flexible architecture enabling:
    * user implemented approaches to core classes, core classes can be replaced via string name in parameter dictionary, eg. user spatial interpolator

    * user developed:
        * custom particle properties derived from other properties though inheritance
        * augment particle velocity given by water_velocity read from hindcast, eg. particle fall velocity
        * modify particle trajectories, eg. resuspension.

* Automated processes to add user developed particle proprieties, velocity, trajectory modifiers, etc , to calculation and output chain. Eg  Requesting a file variable "temperature" from hindcast file by adding to the readers "field_variables" list, will automatically:
    * create a feild of this name
    * interpolate this field to the particle locations at each time step
    * write this particle porpoerty to the output file along with the particle location etc.

* All core and optional classes can be changed or added to list as parameter string using class_name as a string, eg optional particle distance travelled propoerty
* Reduce memory requirement in 'compact_mode',  which only retains active particles, eg. those young enough to be of interest.
* Written in python with numba package for fast in-place operations on particle properties and hindcast's fields based on set of indices arrays.



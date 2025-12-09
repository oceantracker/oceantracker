
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

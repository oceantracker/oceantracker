#####################
Future development
#####################


Future additions
===================

* support for structured grids, eg. ROMS
* option for particle tracking to work natively in lat/log cords
* RK45 solver to allow adaptive time stepping to improve accuracy for those particles where flows are rapidly varying in time or space.
* warn if terminal_velocity movement per time step is larger than median cell height, ie vertical courant number to larger, makes re-suspension unlikely
* Read release points/polygons from file, eg shape files, csv

Possible additions
===================

* merge numerical solver and random walk by moving to numerical solution as a stochastic ODE?



Minor features/fixes
======================

#. support short class_name's given by user ie just AgeDecay,not  oceantracker.particle_properties.age_decay.AgeDecay
#. show dry cells on plots
#. ensure all classes are updated by and .update() method
#. stats/heat maps work from given data as in other ploting
#. status recorded in compact mode is always dead, after removal? so dont apear on plots




#####################
Future development
#####################


Future additions
===================
#. add status_modifier list of classes, to hold tidal stranding, kill old particles etc
#. more post step bookkeeping to pre step bookkeeping to eliminate 2 costly update_cell
#. Add velocity_modfier part prop used inside RK substeps which is updated by velocity_modfier classes every time step, eg terminal velocity
#. find a number container suitable for passing all fields and part prop as a group by name, to allow assess to all and reduce arguments needed
#. Fuse looping for field interpolation for particle properties to reduce RAM-CPU memory traffic
    * kernal version of interpolate fields
    * fuse velocity interpolation and euler step
    * Update field derived particle properties as a group with kernel interpolator
#. make error trapping reponse  more consistent
#. Fuse Runge-kutta steps loops to reduce RAM-CPU memory traffic
    * kernal versions of BC walk and vertical walk
    * fuse BC walk and velocity interpolation using kernals
#. Reader memory shared between parallel cases
#. support for structured grids, eg. ROMS
#. option for particle tracking to work natively in lat/log cords
#. RK45 solver to allow adaptive time stepping to improve accuracy for those particles where flows are rapidly varying in time or space.
#. Read release points/polygons from file, eg shape files, csv
#.  attach interpolator to reader, as step towards working with multiple readers/grids, eg waves on different grid to currents


Possible additions
===================

* merge numerical solver and random walk by moving to numerical solution as a stochastic ODE?



Minor features/fixes
======================
#. automatic particle buffer size estimate factor of 2 too large
#. add class crumb trail method to be displayed in errors and warnings
#. do full parameter set up and release group params and release times in main?
#. use date class consistently through code, ie drop time in independent use of seconds, dates in netcdf files
#. move fom looping over reader buffer to looping over global time step, as step towards shared reader
#. reader buffer as ring buffer
#. move kill old particles to a status modifier
#. add update timer to all classes
#. convert to new status modifier classes
    * cull particles
    * tidal stranding
    * kill old particles
#. support short class_name's given by user ie just AgeDecay,not  oceantracker.particle_properties.age_decay.AgeDecay
#. ensure all classes are updated by and .update() method
#. stats/heat maps work from given data as in other plotting
#. fields manager updated dry cell, move and/or generalize to cases where only tide and depth available
#. velocities as float32 is significantly faster??
#. move to looping over reader global time, remove passing nb, the buffer time step to methods
#. see if numba @guvectorize with threading can increase overall speed on particle operations





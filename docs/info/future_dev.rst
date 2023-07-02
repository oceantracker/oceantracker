#####################
Future development
#####################


Future additions
===================


#. Shared/asynchronous reader to speed solution and save total memory, changes required:
    * set up shared grid and reader field memory in parent and child model runs
    * set up  control variables as shared memory and child and parent responses to reader buffer changes
    * spawn asynchronous model runs, based on parent readers time steps in the buffer
    * have main create info to build reader fields??, then caserunner use this build info, whether shared or not shared, but not grid as it required grid read methods?
    * have main get grid variable dim info , file variable info an give this grid_build info to case_runner with or without shared memory, but not read unless

#. Use multiple hindcasts with different grids, eg wave hindcast and hydro hindcasts on different grids,changes required:
    * attach interpolator to all  fields acting on its buffer,
    * attach reader to all reader fields,
    * reader holds setup interp at given time, not field group manager
    * interpolator class params as a reader parameter
    * field buffer accessed as ring buffer on global hindcast time step calculated from time using reader method
    * move solver to specified time step, ie not substeps, so different hindcasts can have different time intervals
    * dry cell index evaluation at current time step is part of reader as method?, not field group manager
    * share_reader_memory flag move from reader to shared_params

#. velocity interpolator which tweaks flows parallel to faces with adjacent dry cell or land boundary? after random walk velocity is added?
#. Fuse looping for field interpolation for particle properties to reduce RAM-CPU memory traffic
    * kernal version of interpolate fields
    * fuse velocity interpolation and euler step
    * Update field derived particle properties as a group with kernel interpolator
#. make error trapping reponse  more consistent, eg some errors return no info
#. Fuse Runge-kutta steps loops to reduce RAM-CPU memory traffic
    * kernal versions of BC walk and vertical walk
    * fuse BC walk and velocity interpolation using kernals

#. option for particle tracking to work natively in lat/log cords for global scale models
#. Read release points/polygons from file, eg shape files, csv


Possible additions
===================

#. find a numba container suitable for passing all fields and part prop as a group by name, to allow assess to all and reduce arguments needed

#. merge numerical solver and random walk by moving to numerical solution as a stochastic ODE?

#. RK45 solver to allow adaptive time stepping to improve accuracy for those particles where flows are rapidly varying in time or space.




Minor features/fixes
======================
#. Make grid variables which dont vary in time as sharedmemory
#. automatic particle buffer size estimate factor of 2 too large
#. add class crumb trail method to be displayed in errors and warnings
#. do full parameter set up and release group params and release times in main?
#. use date class consistently through code, ie drop time in independent use of seconds, dates in netcdf files
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
#. move velocity reading in al readers to own method to give more flexibility, make it a core particle property with write off by default
#. tidy up case info file, eg have full class params, full params merged in setup in main.py to core and class lists
#. in main do full requirements checked, wit errors communicated, before running up cases
#. to guide users time step choice when using terminal velocities add calc of vertical courant number in top and bottom cell, ie likely the smallest cells)  ( also check vertical random wall size and terminal vel displacement?)
#. move residence time to auto gerate class based on param of polygon release polygon with mutli release groups?
#. add a show_grid to reader, to see grid and use ginput to pick release locations
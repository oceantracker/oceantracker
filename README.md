# OceanTracker

## Fast particle tracking in structure and unstructured grids

OceanTracker is a fast extendable code for offline particle tracking in structured and  unstructured grids [1].

OceanTracker currently  supports strctured grid ROMs and GLORYS(NEMO/COPERNICUS) 
for fixed z level vertical grids and unstructured grids of SCHISM and DELFT3D-FM  

OceanTracker’s speed enables millions of particles to be simulated in unstructured grids. This significantly increases 
the range of particle behaviours that can be modeled and the quality of statistics derived from the particles. 
To eliminate the need to store and wade through the analysis of vast volumes of recorded particle tracks, the code has 
the ability to calculate statistics on the fly, such as heat maps and connectivity between regions.

OceanTracker code is highly flexible and extendable by the user, whether run by a new user with a text file of 
parameters, or by an expert adding their specialised code for novel particle behaviours or statistics, to the computational pipe line


[More about Ocean tracker and gallery](https://oceantracker.github.io/oceantracker/)

[Installing Oceantracker](https://oceantracker.github.io/oceantracker/_build/html/info/installing.html)

[Oceantracker User Guide](https://oceantracker.github.io/oceantracker/_build/html/info/users_guide.html)
  
[Running Oceantracker ](https://oceantracker.github.io/oceantracker/_build/html/info/running_ocean_tracker.html)

[Howto tutorials](https://oceantracker.github.io/oceantracker/_build/html/info/how_to.html)

  
[1] Vennell, R., Scheel, M., Weppe, S., Knight, B. and Smeaton, M., 2021. Fast lagrangian particle tracking in unstructured ocean model grids , Ocean Dynamics, 71(4), pp.423-437.
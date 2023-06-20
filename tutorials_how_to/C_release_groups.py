#!/usr/bin/env python
# coding: utf-8

# # Release Groups
# 
# [This note-book is in oceantracker/tutorials_how_to/]
# 
# A release group is a set of particles released at the same times and location. There can be many release groups. This enables the fate of particles from different origins to be tracked separately within the same computational run. Importantly,  on the fly statistics  are separated into release groups. Eg. gridded statistics return a heat map for each release group, while polygon statistics give the connectivity between each given polygon and each release group.    
# 
# A release group may be 
# 
# * a "point_releases" set points, giving one or more 2D or 3D locations where particles are released. A radius for 2D release around theses point also can be set. 
#     
# * "polygon release", where particles are released randomly within polygon made up of 3 or more 2D points. Particles will not be released in any parts of the polygon outside the domain. 
#     
# For polygons, the vertical release location is randomly chosen in the water column, or user a given  in z range. If the z value of a point release is not given, then the vertical release location is chosen in the same manner. 
# 
# For both types user can specify:
# 
#    * time to start and end the release, or the duration of the release. Defaults are to start at beginning of hindcast and continue until it's end. 
# 
#    * the time between releases, the  "release_interval",  a zero value gives a single release.
# 
#    * the number of particles release each time, the "pulse_size"
# 
#    * whether to release in dry cells, default "allow_release_in_dry_cells" = False
# 
# Plus other options see:
# 
# add links...
# 
# 
# 
# 
#     

# In[1]:


# show example of release types with start and end times, 
#  set up reading geojson/ shapely polygons and show example


# 

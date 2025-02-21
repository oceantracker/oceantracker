.. OceanTracker documentation master file, created by
   sphinx-quickstart on Mon Jul 11 09:12:43 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _home:

#########################
*OceanTracker*
#########################

****************************************************
Fast particle tracking in unstructured grids
****************************************************

.. raw:: html

  <center>
    <video width="70%" controls autoplay loop>
   <source src="./_static/demos/demo02_animation.mp4">
   </video>
  </center>

OceanTracker is a fast extendable code for offline particle tracking in unstructured grids [1]_, which also works with regular grid hydrodynamic models.

OceanTracker's speed enables millions of particles to be simulated in unstructured grids. This
significantly increases the range of particle behaviours that can be modeled and the quality of statistics
derived from the particles. To eliminate the need to store and wade through the analysis of vast volumes of recorded particle tracks,
the code has the ability to calculate statistics on the fly, such as heat maps and connectivity between regions.

OceanTracker code is highly flexible and extendable by the user, whether run by a new user with a text file of parameters,
or by an expert adding their specialised code for novel particle behaviours or statistics, to the computational pipe line.

Code is on `github <https://github.com/oceantracker/oceantracker/>`_ , released under the MIT licence.

====================
Features
====================

* Fast and extendable offline native grid particle tracking for unstructured grids [1] and  stuctured grids.
* Calculate the tracks of millions of particles with fast efficient computation and parallel processing.
* User configurable settings and computational pipeline driven entirely by json or yaml text files.
* Add user defined particle properties and behaviours from parameter text files.
* Native grid particle tracking which preserves the vertical resolution
      * `SCHISM <http://ccrm.vims.edu/schismweb/>` for both  Slayer and LSC vertical grids
      * FVCOM model output, which preserves the resolution of
      * regular native grid ROMs
* Builds heat maps on the fly, without recording particle tracks, also inside polygon counts computed on the fly
* Backward and forward in time particle tracking
* Shoreline stranding of particles by the tide and resuspension from the bottom
* 2D and 3D particle tracking, with option to run 3D as 2D


====================
Architecture
====================

* Implemented in Python
* Driven by parameters in JSON or YAML file, or in code from a Python dictionary
* "helper class" to assist new user build parameters
* Tools to read output, plus plot animations
* Computational pipeline built from user parameters level
* Extendable to create novel particle behaviours, eg. vertical migration of plankton
* Can run particle tracking cases in parallel to further improve computational speed

.. image::  _static/cawthron.jpg
   :target: https://www.cawthron.org.nz/
   :width: 200

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Contents:

   info/about.rst
   info/features.rst
   info/gallery.rst
   info/installing.rst
   info/running_ocean_tracker.rst
   info/how_to.rst
   info/trouble_shooting.rst
   info/parameter_ref/parameter_ref_toc.rst
   info/how_to/D_output_files.rst
   info/change_log.rst


.. warning::

   This is Oceantracker version: |release|.The code its still evolving, documentation needs to be expanded and proof read. If you find bugs, have suggestions or ideas make contact!


.. [1] Vennell, R., Scheel, M., Weppe, S., Knight, B. and Smeaton, M., 2021. `Fast lagrangian particle tracking in unstructured ocean model grids <https://link.springer.com/article/10.1007/s10236-020-01436-7/>`_ ,  Ocean Dynamics, 71(4), pp.423-437.


.. |date| date::



*Last updated:* |date|


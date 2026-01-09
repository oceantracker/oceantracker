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


OceanTracker is a fast extendable code for offline particle tracking in unstructured grids [1]_, which also works with regular grid hydrodynamic models.
It is primarly designed for use in coastal oceans on modest hardware, but handles open ocean, and HPC applications efficency as well.

.. raw:: html

  <center>
    <video width="70%" controls autoplay loop>
   <source src="./_static/demos/demo02_animation.mp4">
   </video>
   <p style="color: #6b7280;"><em>Particles (blue) being being continuously released from green point sources and from within the green polygon. Green particles are currently stranded in dry cells (brown) due to the tide.</em></p>
  </center>

OceanTracker was developed to offer a computationally faster alternative to the existing models and is currently the fastest model for unstructured grids available [2]_.
This enables users to simulate the millions of particles required for many applications on modest office computers while.
For larger applications, OceanTracker offers on-the-fly statistics to eliminate the need to store and wade through the analysis of vast volumes of recorded particle tracks to create e.g. heat-maps or reginal connectivities.

.. grid:: 3
   :gutter: 3

   .. grid-item-card:: Getting Started
      :link: getting_started/getting_started
      :link-type: doc
      :text-align: center

      .. image:: _static/getting_started.png
         :width: 120px
         :alt: Running figure
         :align: center


   .. grid-item-card:: Documentation
      :link: documentation/features
      :link-type: doc
      :text-align: center

      .. image:: _static/user_guide.svg
         :width: 120px
         :alt: Open book
         :align: center


   .. grid-item-card:: API Reference
      :link: documentation/api_ref
      :link-type: doc
      :text-align: center

      .. image:: _static/api.svg
         :width: 120px
         :alt: API details
         :align: center


Its source code is publically available on `github <https://github.com/oceantracker/oceantracker/>`_ , released under the MIT licence.
OceanTracker is under active developement. Feel free to reach out to report issues or to suggest new features.

.. image::  _static/cawthron.jpg
   :target: https://www.cawthron.org.nz/
   :width: 200


.. warning::

   OceanTracker is currently in beta release and its API may change in future releases (see :ref:`change_log` for breaking changes)
   If you find bugs, have suggestions or ideas make contact!


.. [1] Vennell, R., Scheel, M., Weppe, S., Knight, B. and Smeaton, M., 2021. `Fast lagrangian particle tracking in unstructured ocean model grids <https://link.springer.com/article/10.1007/s10236-020-01436-7/>`_ ,  Ocean Dynamics, 71(4), pp.423-437.
.. [2] Vennell, R., Steidle, L., Smeaton, M., Chaput, R., and Knight, B., 2025. `OceanTracker 0.5: Fast Adaptable Lagrangian Particle Tracking in Structured and Unstructured Grids <https://eartharxiv.org/repository/view/8387/>`_ 


.. |date| date::

*Last updated:* |date|


.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Contents:

   overview/overview.rst
   getting_started/getting_started.rst
   documentation/documentation.rst
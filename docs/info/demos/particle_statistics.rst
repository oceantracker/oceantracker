
#########################
Particle Statistics
#########################

Heat maps
====================

.. raw:: html

  <center>
    <video width="95%" controls autoplay loop src="../../_static/demos/demo03_heatmaps.mp4">
   </video>
  </center>


Heatmaps built on the fly with no particle tracks recorded. Options for both time and aged based gridded heatmaps

* class: ``particle_statistics.gridded_statistics.GriddedStats2D_timeBased``
* class:  ``particle_statistics.gridded_statistics.GriddedStats2D_agedBased``

along with counts of particles inside polygons

* class: ``particle_statistics.polygon_statistics.PolygonStats2D_timeBased``
* class: ``particle_statistics.polygon_statistics.PolygonStats2D_ageBased``


.. raw:: html

   <details>
   <summary> code </summary>

.. literalinclude:: ../../../demos/demo_code/demo03_heatmaps.py
    :language: python
    :caption:

.. raw:: html

   </details>

.. raw:: html

   <details>
   <summary> yaml parameters </summary>

.. literalinclude:: ../../../demos/demo_yaml/demo03_heatmaps.yaml
    :language: Yaml
    :caption:

.. raw:: html

   </details>


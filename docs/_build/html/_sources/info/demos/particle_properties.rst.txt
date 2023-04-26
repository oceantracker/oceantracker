
#########################
Particle properties
#########################

Particle properties can easily  add to computation via parameters, eg decaying concentrations,  by listing in particle_properties parameters.
Standard properties include, status, tide, water_depth and  particle age.

Decaying particle
====================
.. raw:: html

  <center>
    <video width="95%" controls muted autoplay loop src="../../_static/demos/demo60_SCHISM_3D_decaying_particle.mp4">
   </video>
  </center>

Decaying particle property used to size and colour  particles. ``decay_time_scale`` parameter = 3.5 hours.

* ``particle_properties.age_decay.AgeDecay``
* demo60_SCHISM_3D_decaying_particle.py

.. raw:: html

   <details>
   <summary> code </summary>

.. literalinclude:: ../../../demos/demo_code/demo60_SCHISM_3D_decaying_particle.py
    :language: python
    :caption:

.. raw:: html

   </details>

.. raw:: html

   <details>
   <summary> json parameters </summary>

.. literalinclude:: ../../../demos/demo_json/demo60_SCHISM_3D_decaying_particle.json
    :language: json
    :caption:

.. raw:: html

   </details>

.. raw:: html

   <details>
   <summary> yaml parameters </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo60_SCHISM_3D_decaying_particle.yaml
    :language: Yaml
    :caption:

.. raw:: html

   </details>

Polygon aware particles
=============================
.. raw:: html

  <center>
    <video width="95%" controls autoplay loop src="../../_static/demos/demo07_inside_polygon_events.mp4">
   </video>
  </center>

Particles with additional inside polygon  property, with optional logging of polygon entry and exit events

* class: ``particle_properties.inside_polygons.InsidePolygonsNonOverlapping2D``
* class: ``event_loggers.log_polygon_entry_and_exit.LogPolygonEntryAndExit``


.. raw:: html

   <details>
   <summary> code </summary>

.. literalinclude:: ../../../demos/demo_code/demo07_inside_polygon_events.py
    :language: python
    :caption:

.. raw:: html

   </details>

.. raw:: html

   <details>
   <summary> json parameters </summary>

.. literalinclude:: ../../../demos/demo_json/demo07_inside_polygon_events.json
    :language: json
    :caption:

.. raw:: html

   </details>


.. raw:: html

   </details>

.. raw:: html

   <details>
   <summary> yaml parameters </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo07_inside_polygon_events.yaml
    :language: Yaml
    :caption:

.. raw:: html

   </details>


Particle Status
=====================
.. raw:: html

  <center>
    <video width="95%" controls autoplay loop src="../../_static/demos/demo56_SCHISM_3D_resupend_crtitical_friction_vel_status.mp4">
   </video>
  </center>

Particles coloured by their status property. Status can be one of following strings

``['unknown', 'bad_cord', 'cell_search_failed', 'notReleased', 'dead', 'outside_open_boundary', 'frozen', 'stranded_by_tide', 'on_bottom', 'moving']``

.. raw:: html

   <details>
   <summary> code </summary>

.. literalinclude:: ../../../demos/demo_code/demo56_SCHISM_3D_resupend_crtitical_friction_vel.py
    :language: python
    :caption:

.. raw:: html

   </details>


.. raw:: html

   <details>
   <summary> json parameters </summary>

.. literalinclude:: ../../../demos/demo_json/demo56_SCHISM_3D_resupend_crtitical_friction_vel.json
    :language: json
    :caption:

.. raw:: html

   </details>

.. raw:: html

   <details>
   <summary> yaml parameters </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo56_SCHISM_3D_resupend_crtitical_friction_vel.yaml
    :language: Yaml
    :caption:

.. raw:: html

   </details>



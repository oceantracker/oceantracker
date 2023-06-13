
#####################
Trajectory modifiers
#####################

Trajectory modifiers classes change the path of particles, examples from standard trajectory_modifiers classes below.

Particle behaviour
====================
.. raw:: html

  <center>
    <video width="95%" controls autoplay loop src="../../_static/demos/demo06_reefstranding.mp4">
   </video>
  </center>

Particles with a random fraction temporarily frozen  on a polygon shaped reef.

* class: ``trajectory_modifiers.settlement_in_polygon.SettleInPolygon``

.. raw:: html

   <details>
   <summary> json parameters </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo06_reefstranding.json
    :language: json
    :caption:

.. raw:: html

   </details>

.. raw:: html

   <details>
   <summary> yaml parameters </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo06_reefstranding.yaml
    :language: Yaml
    :caption:

.. raw:: html

   </details>

Resuspension
====================

.. raw:: html

  <center>
    <video width="95%" controls autoplay loop src="../../_static/demos/demo56_SCHISM_3D_resupend_crtitical_friction_vel_status.mp4">
   </video>
  </center>

Particles with fall velocity and resuspension based on critical friction velocity.

* class  ``trajectory_modifiers.resuspension.BasicResuspension``

.. image::  ../../_static/demos/demo59_crit_shear_resupension_section.jpeg
   :width: 95%

Vertical slice showing one example of a falling particle and resuspension, with particle on bottom during low flows around low and high tides. Blue line is particle status, 10= moving, 6 = on the bottom.

.. raw:: html

   <details>
   <summary> json parameters </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo58_bottomBounce.json
    :language: json
    :caption:

.. raw:: html

   </details>


.. raw:: html

   <details>
   <summary> yaml parameters </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo58_bottomBounce.yaml
    :language: Yaml
    :caption:

.. raw:: html

   </details>

Splitting particles
====================

.. raw:: html

  <center>
    <video width="95%" controls autoplay loop src="../../_static/demos/demo08_particle_splitting.mp4">
   </video>
  </center>

Particles with splitting in two every 6 hours and a 5% chance of dying every 6 hours.

* class: ``trajectory_modifiers.split_particles.SplitParticles``
* class: ``trajectory_modifiers.cull_particles.CullParticles``

.. raw:: html

   <details>
   <summary> json parameters </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo08_particle_splitting.json
    :language: json
    :caption:

.. raw:: html

   </details>


.. raw:: html

   <details>
   <summary> yaml parameters </summary>

.. literalinclude:: ../../../demos/demo_param_files/demo08_particle_splitting.yaml
    :language: Yaml
    :caption:

.. raw:: html

   </details>
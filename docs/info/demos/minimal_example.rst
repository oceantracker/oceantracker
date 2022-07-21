Minimal example
============================


.. raw:: html

  <center>
    <video width="95%" controls muted autoplay loop src="../../_static/demos/minimal_example.mp4">
   </video>
  </center>

Example to show the minmum required to run oceanTracker, using code to both run and plot, or from parameter file.
For this 3D hindcast, grey particles are stranded on the bottom, green ones are stranded on the shore by the tide.


**Run and plot using code:**


.. raw:: html

   <details>
   <summary> code </summary>

.. literalinclude:: ../../../demos/minimal_example.py
    :language: python
    :caption:

.. raw:: html

   </details>


**Run using parameter file:**


    ``python run_oceantracker.py --param_file minimal_example.yaml``

.. raw:: html

   <details>
   <summary> yaml parameters </summary>

.. literalinclude:: ../../../demos/demo_yaml/minimal_example.yaml
    :language: Yaml
    :caption:

.. raw:: html

   </details>

Output is written to directory given set by shared_parameters, ie. a dir named

    ``['root_output_dir']/['output_file_base']``

in this example output is in

 ``output/minimal_example``


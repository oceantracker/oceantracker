Features
================

OceanTracker is primarily designed for coastal environments which is reflected in the supported models and implemented physics.

* We support a large set of **hydrodynamical models**, both with *structured* (i.e. rectangular grid) and *unstructured* (triangular or other multi-nodal cells) grid types.
  Many common models are already supported out of-the-box.
  If yours isn't, feel free to reach out. We are happy to implement new ones.
  The current list includes **SCHISM**, **FVCOM**, **ROMS**, **NEMO** and **GLORYS**, **Delft3D**, and Copernicus i.e. **CMEMS**-catalog.
  We also support nesting grids. E.g. a two coastal high resolution SCHISM models can be nested into a coarser NEMO model.
  For more details see :doc:`supported hydrodynamical models </documentation/features/supported_models>`.

* To enable a large set of research questions we support the following **particle behaviors** and **physical processes**:
  dispersion, settling and re-suspension from bottom based on critical shear velocities, tidal-stranding, varying buoyancies, particles splitting and culling.
  Users can also easily add their own ones to the :doc:`computational pipeline </documentation/features/computational_pipeline>`.

* We are using the model ourselves, and spend quite some time on making its application efficient.
  This is done primarily in two ways: by **reducing user effort** to run and analyze the model and by making the model **computationally fast** to run.

  - We try to keep the time low that a user has to faff with the model configuration through a **modular configuration structure**.
    For large runs, output data management can become the bottleneck.
    We offer :doc:`on-the-fly particle statistics </documentation/features/statistics>` to avoid writing and reading large trajectory files to disk.
    Supported hydrodynamical models are auto-detected and mapped accordingly and particle-tracking output can be quickly plotted with the included plotting routines (see [placeholder] link to the how tos).
  - **Computational efficiency** was the main focus since starting out as existing models weren't fast enough for problems we tried to tackle.
    We believe we are currently the fastest model available for unstructured grids `(Vennell et al., (2025)) <https://egusphere.copernicus.org/preprints/2025/egusphere-2025-4545/>`_.
    This was done through plenty of code optimization (e.g. `BC-walk <https://doi.org/10.1007/s10236-020-01436-7>`_),
    just-in-time compilation using **numba**,
    and built-in **parallelization** via threading. 

.. * Read and visualize model output quickly with .

For more detailed descriptions about individual features see :doc:`feature descriptions </documentation/features>`.

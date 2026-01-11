Supported hydrodynamical models
-------------------------------
The following table shows the currently supported hydrodynamical models.
Feel free to reach out if your model isn't on the list. 
Reads hydrodynamic model output from Schism, FVCOM, plus support for ROMS structured grid  output.

.. list-table::
   :header-rows: 1
   :widths: 20 30 15 15 15

   * - Hydrodynamic model name
     - Description
     - Horizontal grid type
     - Horizontal coordinates
     - Vertical grid type
   * - SCHISM (Semi-implicit Cross-scale Hydroscience Integrated System Model)
     - Schism is a multi-scale, multi-physics hydrodynamic model for simulating flows in the atmosphere, ocean, and coastal regions (Zhang et al., 2016).
     - Unstructured triangular mesh.
     - Geographic and Cartesian
     - S-layer and LSC vertical grids.
   * - FVCOM (Finite Volume Community Ocean Model)
     - FVCOM is a prognostic, unstructured-grid, finite-volume, free-surface, 3D primitive equation coastal ocean circulation model (Chen et al 2003).
     - Unstructured triangular mesh.
     - Geographic and Cartesian
     - Sigma (terrain-following) vertical coordinates.
   * - ROMS (Regional Ocean Modelling System)
     - ROMS is a free-surface, terrain-following, primitive equations ocean model widely used by the scientific community for a diverse range of applications (e.g., Haidvogel et al., 2000).
     - Arakawa C-grid (rectilinear and curvilinear)
     - Geographic
     - Sigma (terrain-following) vertical coordinates.
   * - Delft3D
     - Delft3D is a modelling suite for hydrodynamics, waves and sediment transport. Classic Delft3D-FLOW uses curvilinear structured grids; Delft3D Flexible Mesh (FM) uses unstructured triangular meshes.
     - Curvilinear structured or unstructured triangular mesh (implementation dependent)
     - Geographic
     - Sigma (terrain-following) or z-level depending on implementation.
   * - NEMO/GLORYS/CMEMS catalogue
     - Compernicus Marine Service is public catalogue for near real time and reanalysis products for global and european seas.
     - Arakawa A-grid (rectilinear)
     - Geographic
     - Z-level (fixed depth) vertical coordinates.
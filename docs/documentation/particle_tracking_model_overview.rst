# Overview table of offline Lagrangian models

.. list-table:: Lagrangian Particle Tracking Tools Comparison
   :header-rows: 1
   :widths: 20 10 10 10 10 10 10 10 10 10 10

   * - **Specification**
     - **Ariane**
     - **TRACMASS**
     - **Octopus**
     - **LAMTA**
     - **CMS**
     - **Parcels**
     - **OpenDrift**
     - **OceanTracker**
     - **PyLag**
     - **IndividualDisplacements.jl**
   * - **Website**
     - www.univ-brest.fr/lpo/ariane
     - tracmass.org
     - github.com/jinbow/Octopus
     - bitbucket.org/f_nencio/spasso/overview
     - github.com/beatrixparis/connectivity-modeling-system
     - oceanparcels.org
     - opendrift.github.io
     - github.com/oceantracker/oceantracker
     - pylag.readthedocs.io
     - github.com/JuliaClimate/IndividualDisplacements.jl
   * - **License**
     - CeCILL
     - Open source
     - MIT
     - GNU General Public License
     - GNU GPL v3
     - MIT
     - GPL v2.0
     - *Uncertain*
     - *Uncertain*
     - MIT
   * - **Key Citation**
     - Blanke and Raynaud (1997); Blanke et al. (1999)
     - Döös et al. (2017)
     - Wang et al. (2016)
     - d'Ovidio et al. (2015)
     - Paris et al. (2013b)
     - Lange and van Sebille (2017)
     - Dagestad et al. (2018)
     - Vennell et al. (2021)
     - *No published citation found*
     - Forget (2021)
   * - **OGCMs Supported**
     - NEMO/OPA, ROMS, Symphonie and any C-grid
     - NEMO, IFS (AGCM), MOM, MICOM, POM, HYCOM
     - MITgcm; any C-grid
     - AVISO satellite velocities; any velocity field on A-grids (euclidean or spherical)
     - HYCOM, OFES, NEMO, SOSE, MOM, MITgcm
     - NEMO, OFES, GlobCurrent; customizable to any OGCM with NetCDF data format
     - Any OGCM/AGCM via modular readers; ROMS, NEMO, MITgcm and others
     - ROMS, GLORYS (NEMO), SCHISM, DELFT3D-FM
     - FVCOM, GOTM, ROMS, CMEMS catalog data
     - MITgcm, ECCO, CBIOMES; any gridded ocean/atmosphere model
   * - **Language(s)**
     - Fortran 90/95; Matlab (IDL on request) for visualisation
     - Fortran
     - Fortran
     - GNU/Octave and C++
     - Fortran
     - Python user interface, auto-generated C
     - Python
     - Python with Numba
     - Python and Cython
     - Julia
   * - **Primary Use**
     - Offline calculation of 3D streamlines in the velocity field at any scale (regional, basin, global); volume transport calculations
     - 3D water mass pathways, particle/tracer dispersion
     - 3D watermass pathway, particle/tracer dispersion, cross-frontal transport, Argo float simulation
     - Compute satellite based Lagrangian diagnostics to optimize sampling strategy of mesoscale-based field campaign and support interpretation of in-situ observations
     - Dispersion, connectivity, fate of pollutants; Individual Based Modelling
     - Large scale oceanography; Individual Based Modelling; teaching (via customizable interface)
     - Oil spills, search and rescue, larvae drift, general ocean/atmosphere particle tracking
     - Fast particle tracking in structured and unstructured grids; marine ecology, larval dispersal
     - Marine applications; particle tracking in coastal regions; larval transport
     - Climate system particle tracking; ocean/atmosphere transport; plastics, plankton, dust
   * - **Advection Method**
     - Analytic
     - Analytic
     - RK4
     - RK4
     - RK4
     - RK4, RK45, Explicit Euler; extensible interface for custom advection methods
     - RK2 (Runge-Kutta 2nd order), Euler forward
     - RK4
     - RK4 (Adv_RK4_2D, Adv_RK4_3D)
     - ODE solvers via DifferentialEquations.jl (e.g., Tsit5)
   * - **Diffusion Method**
     - No diffusion (purely kinematic method)
     - Brownian motion for background diffusion with random displacement or randomly added velocities
     - Brownian motion for background diffusion, random displacement within the mixed layer
     - Random walk optional
     - Brownian motion for background diffusion, random displacement within the mixed layer
     - Extensible interface for Random Walk and custom behaviour
     - Random walk with vertical and horizontal turbulent mixing; Brownian motion
     - Random walk, turbulent mixing parameterization
     - Random Displacement Model with diffusion tensor
     - *Uncertain - extensible via custom kernels*
   * - **Grids Supported**
     - Arakawa C, also tested with Arakawa B interpolated on C-grid, partial cells supported
     - Arakawa A, B, C. Spatially and temporally varying vertical grids supported (partial cells, z*, sigma, hybrid) including those for AGCMs
     - Arakawa C
     - Arakawa A
     - Orthogonal (rectangular) Arakawa A, B and C
     - Arakawa A, B and C; unstructured meshes planned
     - Any grid type via modular readers; curvilinear, regular lat-lon
     - Structured grids (Arakawa C); unstructured grids
     - Arakawa A, C grids; structured and unstructured
     - Arakawa C-grids; MeshArrays.jl for various grid types
   * - **Key Strengths**
     - Almost 25 years of experience with core of the code; easy-to-install, easy-to-use; fast analytical solution; no coast crash; qualitative mode (full details of selected trajectories) and quantitative mode (volume transport calculations); compatible with the conservation laws of the OGCM
     - Volume conserving, fast analytical solutions without intermediate time steps, works with both OGCMs and AGCMs
     - Fast using Fortran, supports openMP
     - Designed to work out-of-the-box with AVISO surface geostrophic velocities. Already configured to compute a broad range of Lagrangian diagnostics (i.e. Finite Time/Size Lyapunov Exponents; longitudinal and latitudinal origin of particles; time of particle retention within mesoscale eddies etc.)
     - Modular, fast, parallel; Multigrid support; Used in a wide variety of contexts, from marine ecology to physical oceanography
     - Ease-of-use, customizable extension interface and automated performance optimization
     - Highly modular and flexible; operational use for emergency response; easy setup; GUI available; supports multiple data sources
     - Extremely fast (2 orders of magnitude faster than some codes); on-the-fly statistics; modular pipeline; supports millions of particles on single core
     - Fast (Python/Cython); MPI parallel; extensible; supports Stokes drift and windage; flexible
     - Native Julia performance; integrates with Julia ecosystem; global climate model support; MeshArrays.jl interoperability
   * - **Shortcomings**
     - No parallel mode; trajectory scheme is somewhat crude beyond the context of 3D water mass tracing
     - Need of improving the diffusion method
     - Non-scalable parallelization, not very efficient in reading large model output
     - Particle advection only 2D; cannot be run in parallel
     - No support for non-orthogonal grids; parallel implementation is heavy on I/O
     - Not yet parallel; support for unstructured meshes in progress
     - *Uncertain about specific limitations*
     - Not yet parallel (as of published version)
     - *Limited documentation on scalability*
     - Relatively new package; smaller user community than established codes
---

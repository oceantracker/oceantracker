Integration methods
-------------------

We support three time integration methods
- Runge-Kutta 4th-order (RK4)
- Runge-Kutta 2nd-order (RK2)
- Euler forward

The current default is RK4, as these seems to be the community standard.
However, we recommend to use RK2 as e.g. `Mork et al 2025 <https://doi.org/10.5194/egusphere-2025-2109>`_ highlighted that in dispersive coastal dyanamics the errors scale with O(2) anyway.
E.g. RK4 is in most model scenarios not improving model accuracy.
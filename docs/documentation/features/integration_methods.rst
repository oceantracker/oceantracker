Integration methods
-------------------

We support three time integration methods for advecting particles with the water velocity (plus any velocity modifiers):

- Runge-Kutta 2nd-order (RK2, midpoint method), the default
- Runge-Kutta 4th-order (RK4)
- Euler forward (RK1)

The default is RK2. OceanTracker interpolates the hydrodynamic model's velocities linearly in space and time,
and with linear interpolation RK4 does not improve accuracy over RK2:

- `Mørk, Nordam and Rühs (2025) <https://doi.org/10.5194/gmd-18-7831-2025>`_ showed that the discontinuous derivatives of linearly interpolated velocity fields
  limit RK4 to second-order accuracy.
- The `KELP v1.0 <https://doi.org/10.48550/arXiv.2611.18528>`_ preprint (Kuznetsov et al., 2026) found that with linear interpolation in time RK2 and RK4 gave the same error
  whatever the time step, as the interpolation error limits the accuracy whatever the order of the integrator.

RK2 needs two velocity interpolations and cell searches per time step, compared with four for RK4, so it is considerably faster.
An RK2 run with half the time step therefore does the same number of velocity interpolations as an RK4 run with the full time step.

Versions before 0.5.3.12 used RK4 as the default. To reproduce results from these versions, set the order explicitly using the solver's ``RK_order`` parameter:

.. code-block:: python

    ot.add_class('solver', RK_order=4)

or, when running with a parameter dictionary:

.. code-block:: python

    params['solver'] = {'RK_order': 4}

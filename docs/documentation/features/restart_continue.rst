Model restart and continue feature
----------------------------------

Some questions require models to be run for a long time, with either high particle counts or small time steps.
In these cases, the model run time (wall time) can be relatively long, i.e. weeks or months.
Therefore, having to rerun models can be problematic.

We typically encountered three problems in such contexts:
1. Machine failure, e.g. an HPC/cloud session running out of time, a power outage or another hardware issue.
2. Scope creep, e.g. when the results from the current simulation generate interest in a longer simulation.
3. Misparameterisation, e.g. due to user error, means that the model you are running is not producing the intended results.


Model restart, i.e. 'hotstart'
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the event of a machine failure, it would be ideal to resume the simulation from where it left off.
To this end, we have introduced a 'restart' feature that can be enabled by setting a 'restart_interval' parameter.
This parameter defines the time interval between the current model state being written to disk.
The data is stored in a 'saved state' directory in the root output directory.
When a simulation fails, the user simply reruns the exact same model configuration.
If a restart interval has been reached, i.e. if a model state has been written to disk, oceantracker will locate that state, load it and resume the simulation from that point.
Currently, only tracks and age-based statistics are restartable. Runs with time-based statistics have not yet been implemented and will fail.
Contact us if you would like this feature.



Continue the simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another scenario is that you would like to resume a simulation that has already been run.
This is sometimes the case when the maximum session length on a cluster or HPC machine is insufficient for the full simulation duration, or when the current simulation results raise questions about later timeframes.
By default, runs are not continuable because writing the model state to disk can create large volumes of data that clutter the storage space. If the disk size is limited, this can even cause the simulation to fail because results can no longer be written to disk.
If you expect to want to continue a run, you can enable this by setting the 'continuable' parameter to true.
This writes the model to disk at the last time step, similarly to the 'saved state' in the restart feature.
If you then wish to continue a run that has been configured to be continuable, you can point the next simulation at the previous one by providing the path for "run_to_continue" in the model configuration.
Currently, only tracks and age-based statistics are continuable. 
Runs with time-based statistics have not yet been implemented and will fail.
Contact us if you would like this feature.

Preliminary results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some scenarios, it can be helpful to take a look at preliminary results, e.g. to validate that the model is configured correctly and does what it is intended to do, at least superficially.
This has been drafted but not yet properly implemented, as this problem can also be solved more tediously using the 'continue' feature.
However, if you would like to use it, please get in touch.







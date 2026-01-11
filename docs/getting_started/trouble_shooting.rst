################
Troubleshooting
################

Sadly, things usually don't run smoothly on the first try.
There are many things that can go wrong when configuring OceanTracker.


First step:
===================

If your run fails, carefully look back at the screen output and find the first error flagged.
Some errors create additional errors, but typically it's only the initial one that needs to be addressed.
If you can't identify the source of the error, try to reduce the complexity of the problem until you end up with a minimal example.

There are two types of problems that you can run into, those that we anticipated, and those we didn't.
For the more common use cases, we tried to catch errors and exit the simulation gracefully, while providing guiding messages to the screen output that should help identifying the problem.
The screen output is also written to the root output directory (look for a file named _log.txt).
For those that we didn't anticipate, there still is the Python traceback output that is also written to the log.
There is also a third kind of error. The one that isn't reported at all. I.e. the simulation runs successfully, but something seems off anyway.
These are typically the hardest ones to debug because there is rarely a clear indication of what went wrong.
We'd recommend to frequently run the model when assembling the different components of the configuration, to catch those issues early on with an identifiable source.

Anticipated errors:
===================

These are typically errors in the settings, i.e. parameters supplied to OceanTracker, or issues with the hindcast data.
They normally also have traceback information and come with both, with a message and a hint about what to do about it.
Some problems are also defined to only trigger warnings instead of errors that would stop the simulation.
These are generally for situations when something in the configuration is odd, e.g. when one of the release locations is outside of the domain.
This might have not been intended, but maybe there are simply some locations you didn't bother to clean properly.

Unexpected errors:
==================

These are raised errors, those that generate a full stack traceback.
Those are either misconfigurations we didn't anticipate, or issues or bugs in OceanTrackers code.
Take a moment to check if it is a misconfiguration issue, and if not, please reach out so that we can fix the issue – or send us a pull request if you fixed it yourself.
Feel free to also report misconfiguration issues that you think we should have caught.

Reporting an error:
===================

When reporting an error, please:

1. Rerun the code with setting ``debug = True``, which may give more informative error messages.
2. Add the following files to the report:
    * ``*_log.txt``, screen log
    * ``*_caseInfo.json``, lots of useful info
    * ``*_raw_user_params.json``, the raw user supplied settings/parameters

Either send them via mail, or open a `GitHub issue: <https://github.com/oceantracker/oceantracker/issues>`_.
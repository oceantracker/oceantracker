##########################
Trouble shooting
##########################

There are a number of ways a run can produce error messages.
Known errors caught by OT should have  graceful exit error.
Others with trace back are likely
aspects that OT is not yet aware of, or code bugs for the developer to fix.
Warnings or Notes do not cause OT to exit.

First step
===================

Carefully, look back at the screen output or *_caseLog_log.txt
file, and find the first error flagged.
Some errors spawn other errors, so look back before the last reported error.

Anticipated errors
===================

These are errors that results from internal checks done by OT.
They are usually to to with errors in the settings or parameters supplied or issues with the hindcast.
They normally don't have traceback information and come with both a message and a hint about what to to about it.

Unexpected errors
===================

These are raised errors, those that generate a full stack traceback.The are likely
OT code issues or bugs. Which could be due to:

* Unanticipated use of parameters, not trapped by internal checks.

* Readers issues with hindcast not trapped by code. e.g. a variant of the hindcast file format that OT has not yet been tested with.

* Bugs, such as array out of bounds errors, or unknown dictionary keys.

These errors need to be reported to the developer to fix.


Reporting an error
===================

In reporting an error to the developer, please

* Rerun the code with setting debug = True, which may give more informative error messages.

* Send the to developer the following files:

    # *_caseLog_log.txt, screen log

    #  *_caseInfo.json, lots of useful info

    # *_raw_user_params.json, user supplied settings/parameters

    # *_runInfo.json,  global information about the hindcast and run

* If requested also give access to

    * all the  output files, eg. tracks etc

    * a sample of the hindcast in order to reproduce the bug, with the given *_raw_user_params.json file.


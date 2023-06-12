Run in parallel
===============

[This note-book is in oceantracker/tutorials_how_to/]

Running in parallel can be done using the “run with parameters”
approach, not the helper class method. Simply build a list of “cases”
parameters , then pass this list, eg. main.run(case_list). This the
output files for each case will be tagged with a processor number.

The cases can be different, eg have differ release groups etc. A small
number of settings must be the same for all cases, eg. setting
“root_output_folder” must be the same for all cases. These setting will
be taken from the first case. Warnings are given if trying to use
different values of these settings than that given in the first case.

Add example below

.. code:: python

    # under develop







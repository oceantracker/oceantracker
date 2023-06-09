.. code:: python

    # running in paramlet 
          4. "case_list_params", these are the paramters as above which will run cases run in parallel.  This is a list of top level parameters used for each case run in paralle. The top level  essttial user given defaults for those in each case. Eg. a case may have its own time_step, or add items to the class_lists eg releases_groups,  which are used with the case.  For technical reasons, a small numer of parameters cannot be set for an individual case, eg "back_tracking", atempting to set these with raise and error. See running in parallel tutourial for more details.







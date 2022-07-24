##########################
Parameters overview
##########################


OceanTracker is structured to run one more "cases" of particle tracking, each with their own set of parameters.
The parameters are a python dictionary of key-value pairs
(parameters  in JSON or Yaml file  are converted to a python dictionary).
Thus key-value pairs of parameters setup the computations. The top level parameter dictionary, may contain other nested parameter dictionaries, or lists of other parameter dictionaries.


Top level params
=================================
The top level parameter dictionary has the structure:

.. code-block:: python

    {   'shared_params': { 'root_output_dir': 'my_output', .... } # common to all cases
        'reader': {'class_name':,.... } ,           # shared hindcast reader
        'base_case_params': {},                     # user given defaults for all cases
        'case_list': [],                            # list of individual case parameters
     }


* 'shared_params' are parameters used  for all cases
* 'reader' are parameters for the hindcast reader, which reads variables from a set of hindcast files and is shared by all cases, eg input_dir and file_mask
* 'base_case_params' are parameters common to all cases,
* 'case_list' are parameters unique to each individual case which will also overwrite any also given in base_case_params.

For single case parameter tracking, the user only needs to set 'base_case_params'.
OceanTracker will automatically create a case with these parameters. A case list allows multiple cases to be run at the same time. Theses case will be run in
in parallel if shared_param 'processors' > 1, otherwise they will run in serial.

Case level params
=================================

Both 'base_case_params' and those within the 'case_list'  have the exactly the  same parameter structure.

.. code-block:: python

    {    'run_params' : {}
        # core classes
       'solver': {},
       'field_group_manager':{} ,
       'interpolator': {} ,
       'particle_group_manager': {},
       'tracks_writer':   {},
       'dispersion':      {},
       'particle_release_groups':  [],  # required
     # below are optional user classes held in named lists
       'fields':          [],  # prop calculated from other fields  on reading
       'particle_properties':     [], # user added particle properties, eg DistanceTraveled
       'velocity_modifiers':      [], # user added velocity effects, eg TerminalVelocity
       'trajectory_modifiers':    [], # change particle paths, eg. re-suspension
       'particle_statistics': [],# heat map inside polygon statitics calculated on the fly
       'event_loggers':           [], # writes events files ,eg PolygonEntryExit
       'particle_concentrations': [], # writes concentration of particles within triangles of the grid
                                       # and other properties calculated on the fly.   files ,eg PolygonEntryExit
       }


* 'run_params' are case  specific parameters, eg 'duration'
* the next block are core classes  parameters, eg set turbulent eddy viscosity in random walk 'dispersion'
* 'particle_release_groups' is required. It  is a list of parameters detailing where and when particles are released from points or within a polygon. The list allows particles from  each release group to be followed separately, eg. counts in  statistics are separated by release group.
* The following are optional lists of parameters for classes which create new particle properties, calculate statistics, or modfiy how the particles move


Defaults
=================================

All parameters, at top level or lower level, or within lists, are dictionary like, ie. key-value pairs.
A value which is a dictionary is treated as a nested parameter dictionary of key-value pairs.

The values at the ends of any top level dictionary or nested parameter dictionary
have specified default values associated with their key, which are used if none is provide by the user.


Checking
=================================
Any user given values are checked to ensure they are the required data type,  are in the range of acceptable values, etc.
For a few keys, a value must be supplied by the user (eg. input_dir of hindcast files). If these are not given an "is_required error" will be generated.

The user is warned of any unexpected keys found within the parameters, ie those not in the default parameter dictionary.


class_name parameter
=================================

To give flexibility the classes which  make up the particle tracking computational pipeline
are added via their class_name parameter given as a string, eg.

``"class_name": "oceantracker.particle_release_groups.polygon_release.PolygonRelease"``

which is used to import the class. This enables users to freely add the capabilities needed.
In this case there might be releases from several different polygons, each with their individual release rates etc,
each added by their parameters in the particle_release_groups list.

Adding  via a string also allows users to create their own variants of the classes,
which inherit most of their functionality from their parent class, but are  tweaked to have behaviours or functionality
to suit the user. These new particle properties are added to the computational pipeline with their parameters.
Provided they are in the current working dir or accessible via the python path,
these user added classes, along with all other classes, are imported using their class_name string.

An example below is the class which adds the 'AgeDecay' particle property. The important method is its update()
which calculates the current amount of the property remaining based on the core particle property 'age' and exponential decay.
Age is part of the same computational  pipeline as AgeDecay, like a particle's location property 'x',  another core property.
Core particle properties are updated before those added by the user.

The mechanics of accessing AgeDecay's data and writing it to the output file are done with methods inherited from the
ParticleProperty base class ``oceantracker.particle_properties._base_properties.ParticleProperty``,
all overseen by the core ParticleGroupManager class.

Once the 'AgeDecay' class is imported, its parameters are merged with the defaults, it is then initilaized and added to
the computational pipeline by the ParticleGroupManager. Then it will automatically:

* be updated each time step
* be written to the output file along with 'x' and other properties (unless its 'write' parameter is False)
* if requested, have statistics such as heat maps automatically calculated and written to output files on the fly
* its values can be access by other particle properties, which may depend on it (eg. age_decay particle property depends on the 'age' property)


.. literalinclude:: ../../../oceantracker/particle_properties/age_decay.py
    :caption:
    :language: python

####################
Code Structure
####################

Ocean tracker is structured to achieve two main objectives:

	* Be easily extensible by advanced users through user supplied code, e.g.. a user's custom particle resuspension model.

	* To be run using a single parameter set. This enables
        * OceanTracker to be used by non-coders
        * Web based particle tracking on demand for both non-coder and advanced users


These two objectives may conflict. Both are made possible by naming the classes used for a specific run within the parameter file. The named classes, whether OceanTrackers version or the user's version are imported for use on setup. Users can adapt classes by inheriting OceanTrackers version and overriding required class methods with their own versions, and then naming their class in the  "class_name" parameter. Adaption would often involve overriding the classes update() method to meet the user's needs.

Parameters may be contained in a json or yaml file, or constructed in code as a Python dictionary.  There are different types of parameters, each given as a dictionary of key/value pairs, nested within the overall parameter dictionary.

		#. over all control parameters, eg location of hindcast, output folder,  maximum run times etc.
		#. Core class parameters, for which only one is given, eg solver class which does the numerical integration over time, hindcast reader class or dispersion classes. 
		#. Lists of class parameters. For example,  a list of particle release group classes, specifying a point or polygon release at given locations,  times and frequencies.  
		
	
Types of Class
#################

There are many types of classes a each performing different role within OceanTracker, e.g. trajectory_modfiers which change the path followed by particles, such as resuspension from the bottom. The class types are  directly reflected in the structure of the parameter file. Class types, like solver, or particle_statistics, each  have default parameters which are overwritten by user supplied values, then imported to run the simulation.  A full set of class types  and their roles is given in at ....

todo: more??

Making a user version of a class 
######################################################
		
Classes have many methods,  the key ones likely to overridden by teh user by class inheritance are given below. Most often a user will start by inheriting a working class eg. PointReleaseGroup, and tweak its methods to meet their need. Most classes types have a _base class for their type, which outlines key methods required for that class type. These methods most likely to overridden and their roles are: 

    * __init_(): sets  default parameters for the class and enables parameter checking using .add_default_params()  method.    Note this must always cal is supper  __init_() to acquire its parents default parameters.  Todo- better if set_defalts call its parent version??

    * check_requirements():  checks integrity of classes and throws errors if any found by:

    * check if  required files, particle properties need to implement this class are available, or must be only use for 3D hindcasts using the check_class_required_fields_prop_etc(): method
        * any other requirements specific to this class to enable it to run

    * initialize():  Any processes needed to set up the class, e.g. initialize variables allocate arrays, add required particle custom properties or fields need for this class etc.
	
	* update():  Updates the class if required, eg. updates a particle property at each time step, or a a custom field calculated from other when fields are read from a hindcast file.

	* close(): Any tidy up, e.g. any final calculations, writing final output and closing files,

To loading a class OceanTracker does the following:

	#. Merges users supplied parameters with class defaults and does basic checks on the parameters using merge_with_class_defaults() method, e.g.. data has rewired tyre, or if it is required but not specified by user.

	#. imports the class given by the "class_name" parameter as text

	#. invokes check_requirements() method to ensure class has access to the variables it requires to run

	#. invokes initialize() method to do required set up of class variables.
	

Readers Role/Construction
#######################

A reader's role is to access  the hindcasts grid and field variables. It role is to: 
 
    * read the hydrodynamic model grid into core variables and add required variables, such as adjacent triangles map.
		
    * read field variables that may 2D/3D time independent/dependent variables, which may be vectors or scalars  to be interpolated to particle locations. The reader maps the components of vectors to the variable names used internally within the code.  To standardise access by looping Numba code, all fields are stored as 4 arrays, with dimensions (time, node, z, vector components).  Scalers, time-independent, and 2D fields have unit dimension size within the 4D array storage.


Reader required methods
##########################

	* read_nodal_x_float32() :  Read nodel (x,y)  as N by 2 vector of node cords as float64
    * read_triangles_as_int32(): read triangulation as M by 3,  and split any quad cells into new triangles
    * read_water_depths_as_float16(): read water depths at nodes as N array

read_grid(): creates reader classes self.grid dictionary with keys

	* 	'x',

	* 'triangles', the triangulation of grid node numbers (zero based) as int32, normally M by 3, but if M by 4, then assumes some cells area quad cells must be split into triangles and  'triangles' using split_quad_cells ( which records split cells to allow cell data to be reformated on read

    * 'water_depth', depth at nodes as float16, below fixed datum, ie not  time varying

    * if 3D set up empty space for 'zlevel', the vertical location of cell boundaries as float16,

	* 'bottom_cell_index' index ( zero based) of first zlevel where bottom  N array of  int32, if missing fill with zeros.

	* set up space 	for 'dry_cell_index' as int8, 0 if wet, 127 if cell dry.

read methods for time variable data

	* read_file_field_variable_as4D: get nodal values of fields, which may be time varying/non-time variables or 2D/3D

    * read_zlevel_as_float32 if 3D hindcast

    *	read_dry_cell_index as int8, 0= wet ,127 = dry

To do
######

* add a node or cell data,  flag to feild info, to auto  

* class paramters
* fields, vectors, partcle propteties
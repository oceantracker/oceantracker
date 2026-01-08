Readers of hydrodynamical model data
------------------------------------

By default a "flexible reader" is used.
I.e. if you don't specify a certain reader OceanTracker will skim the files in the input directory
and, assuming you hindcast follows the standards of your model, automatically detects the correct reader.

The names of the implemented readers are
* DELFT3DFMreader
* FVCOMreader
* GLORYSreader
* ROMSreader
* SCHISMreaderV5
* SCHISMreader

If your hindcasts varies from the default naming scheme you can remap variables names using.
If you have a completely unsupported hindcast or e.g. some toy data you can attempt maping the *GenericUnstructuredReader* to get it to work.
But feel free to reach out to us. We'd be happy to help and add support for new models.


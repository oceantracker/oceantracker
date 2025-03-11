
Build oceantracker conda environment
________________________________________

To ensure python/ module compatibility, recommendation is to build a conda virtual environment with the given environment.yml file

1. Install 
    
    Install/update anaconda or miniconda if not already available


1. Change dir to where oceantracker files will be stored , e.g. 

    ``cd  mycodedir``

2. Ensure git is installed, then clone repository

    git clone https://github.com/oceantracker/oceantracker.git

3. Change dir to oceantracker package folder, eg.

    ``cd ./oceantracker``

3. Manually build a Conda environment

        ``conda create -n oceantracker python=3.10`` 

    Note: Oceantracker will work in Python 3.11 and 3.12, Python version 3.10 is preferred, as currently  not all required external imported  packages for plotting work in 3.11

    Activate new environment

        ``conda activate oceantracker``
   
   Then install these packages

   ``conda install conda-forge::numba``
         
   ``conda install anaconda::numpy`` 
 
   ``conda install conda-forge::netcdf4``

   ``conda install anaconda::xarray``     
        
   ``conda install anaconda::scipy``

   ``pip install pyproj``

   ``conda install anaconda::pyyaml``

   ``conda install conda-forge::psutil``

   ``conda install conda-forge::python-dateutil``

   ``conda install conda-forge::matplotlib``

7. Make oceantracker package findable
   
   From root dir of oceantracker package

   ``pip install --no-deps -e .`` 

8. To add ability to make animation movies if needed

   ``conda install conda-forge::ffmpeg``

9. To work with iPython/Jupyter notebooks

   ``conda install anaconda::ipykernel``
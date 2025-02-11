
Build oceantracker conda environment
________________________________________

To ensure python/ module compatibility, recommendation is to build a conda virtual environment with the given environment.yml file

Due to version dependencies of modules outside oceantracker, it curently only works with python 3.10 and numpy < 1.24, and not yet python 3.11 

1. Install 
    
    Install/update anaconda or miniconda and git if not already available


1. Change dir to where oceantracker files will be stored , eg. within

    ``cd  mycodedir``

2. Ensure git is installed, then 

    git clone https://github.com/oceantracker/oceantracker.git

3. Change dir to oceantracker folder, eg.

    ``cd ./oceantracker``

3. Manually build a Conda environment

        ``conda create -n oceantracker python=3.10`` 

    Note: Use python version 3.10 as not all required external imported  packages work in 3.11

    Activate new environment

        ``conda activate oceantracker``
   
   Then install these packages


      ``conda install anaconda::numpy=1.26``

      ``conda install conda-forge::numba``
 
      ``conda install conda-forge::netcdf4``

      ``conda install anaconda::xarray``     
        
      ``conda install anaconda::scipy``

      ``pip install pyproj``

      ``conda install anaconda::pyyaml``

      ``conda install conda-forge::psutil``

      ``conda install conda-forge::python-dateutil``

      ``conda install conda-forge::matplotlib``

7. Make oceantracker package findable
   
   From root dir of oceantracker 

   ``pip install --no-deps -e .`` 

8. To add ability to make animation movies if needed

   ``conda install conda-forge::ffmpeg``

9. To work with iPython/Jupyter notebooks

   ``conda install anaconda::ipykernel``
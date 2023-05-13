Build oceantracker conda environment
________________________________________

5 Steps!

1. Install 
       
       conda or miniconda
       
       install git if not already available


1. Change dir to where oceantracker files will be stored , eg 

    ``cd  mycodedir``

2. Ensure git is installed, then 

    ``git clone https://github.com/oceantracker/oceantracker.git``

3. Change dir to oceantracker folder, eg.

    ``cd ./oceantracker``


4. Either: Make conda  environment from given file

Note: In Windows may need to run conda prompt window as administrator to install packages

   From root dir of oceantracker package run 
    
           ``conda env create -f environment.yml``
    
   Activate new environment

        ``conda activate oceantracker``

    
5. Or : Manually build Conda environment

        ``conda create -n oceantracker python=3.10`` 

   Activate new environment

        ``conda activate oceantracker``
   
   Then install these packages

      ~~~  
        conda install -c conda-forge numba
        conda install -c conda-forge netcdf4
        conda install -c anaconda numpy
        conda install -c anaconda scipy
        conda install -c conda-forge pyproj
        conda install -c anaconda pyyaml    
        conda install -c anaconda psutil
        conda install -c conda-forge matplotlib
        conda install -c conda-forge python-dateutil
        conda install -c anaconda scipy
        conda install -c conda-forge geojson
        ~~~


6. Make oceantracker package findable
   
   From root dir of oceantracker 

   ``pip install --no-deps -e .`` 

8. To add ability to make animation movies if needed

   ``conda install -c conda-forge ffmpeg``

9. To work with iPython/Jupyter notebooks

   ``conda install -c anaconda ipykernel``
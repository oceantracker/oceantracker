Install using pip 
________________________________________


1.    Install/update anaconda or miniconda if not already available
    
        https://www.anaconda.com/docs/getting-started/miniconda/install

2. create veritual enviomnent ( python 3.10 recommended)
    at command prompt  :  ``conda create -n oceantracker python=3.10``
3. Activate new environment   ``conda activate oceantracker``
4. install ocean tracker    ``pip install oceantracker``

Note: 
- Oceantracker will work in Python 3.11 and 3.12, Python version 3.10 is preferred, as currently  not all required external imported  packages for plotting work in 3.11
-  may need to run Conda as Admin on  Windows
- pip install will not include how_to notebooks and the demo hindcasts they use 

Install using git repository
________________________________________

this includes how_to notebooks and the demo hindcasts they use

1. Change dir to where oceantracker files will be stored , e.g. 

    ``cd  mycodedir``

2. Ensure git is installed, then clone repository

    git clone https://github.com/oceantracker/oceantracker.git

3. Change dir to oceantracker package folder, eg.

    ``cd ./oceantracker``

3. Manually build a Conda environment
 

        ``conda create -n oceantracker python=3.10`` 



    Activate new environment

        ``conda activate oceantracker``
   
   Then install these packages 

   ``conda install conda-forge::numba=0.56.4``  if using python 3.10

   ``conda install conda-forge::numba``  if using python 3.11 or higher
         
   ``conda install anaconda::numpy`` 
 
   ``conda install conda-forge::netcdf4``

   ``conda install anaconda::xarray``     
        
   ``conda install anaconda::scipy``

   ``conda install conda-forge::pyprojy``

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
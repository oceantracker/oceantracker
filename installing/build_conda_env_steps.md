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

    cd ./oceantracker


4. Make conda  environment

    1. Easy way t
    
    
    From root dir of oceantracker package run 
    
        ``conda env create -f environment.yml``
    

    
    2.  Manual steps
    
    
        ~~~        
        conda create -n oceantracker python=3.10 
        conda activate oceantracker   
        conda install -c conda-forge numba
        conda install -c anaconda numpy
        conda install -c conda-forge netcdf4
        conda install -c anaconda scipy
        conda install -c conda-forge pyproj
        conda install -c anaconda pyyaml    
        conda install -c anaconda psutil
        conda install -c conda-forge matplotlib
        conda install -c conda-forge python-dateutil
        conda install -c anaconda scipy
        ~~~


5.  Make oceantracker module findable

``pip install --no-deps -e`` 
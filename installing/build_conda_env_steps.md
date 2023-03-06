
# get ocean tracker from github

Change dir to where oceantracker files will be stored , eg 

``cd  mycodedir``

Ensure git is installed, then 

``git clone https://github.com/oceantracker/oceantracker.git``

Change dir to that with oceantracker

cd ./oceantracker


# Create Conda Environment 

    # Create from ocean tracker 

            
``conda create -n oceantracker python=3.10.8``

``conda activate oceantracker``

# install required modules

``conda install -c anaconda scipy``

``conda install -c conda-forge matplotlib``

``conda install -c conda-forge netcdf4``

``conda install -c numba numba``

``conda install -c conda-forge psutil``

``conda install -c anaconda pyyaml``

``conda install -c conda-forge pyproj``




Make  dir to that with oceantracker
pip install --no-deps -e 
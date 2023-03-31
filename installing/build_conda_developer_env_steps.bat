conda create -n dev-oceantracker python=3.10.8
conda activate dev-oceantracker
conda config --add channels https://conda.anaconda.org/conda-forge
conda config --add channels https://conda.anaconda.org/domdfcoding
conda install -c anaconda numpy
conda install -c anaconda scipy
conda install -c conda-forge netcdf4
conda install -c conda-forge matplotlib
conda install -c conda-forge netcdf4
conda install -c conda-forge pyproj
conda install -c numba numba
conda install -c conda-forge psutil
conda install -c anaconda pyyaml
conda install -c conda-forge pyproj
conda install -c anaconda sphinx
conda install sphinx-toolbox
conda install -c conda-forge rst2pdf
conda install -c anaconda line_profiler
conda install -c conda-forge pyinstrument
git clone https://github.com/oceantracker/oceantracker.git
cd ./oceantracker
pip install --no-deps -e .





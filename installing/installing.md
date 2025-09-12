# Installation

We recommend using Python environments to install OceanTracker.
This ensures that the versions of the necessary packages are handled correctly and makes the entire process more reliable for users and developers.
The recommended way to create these environments is by using Mamba, a fast version of Anaconda.

You can find the documentation on how to install mamba [here]
(https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html)

## Install using pip 

If this is your first time using OceanTracker, the easiest way to install it is via pip.

```bash
# Create a new conda environmen
mamba create -n oceantracker
mamba activate oceantracker

# Install dependencies via conda
mamba install -c conda-forge numba numpy netcdf4 xarray scipy pyproj matplotlib pyyaml psutil

# Install oceantracker via pip
pip install oceantracker
```

Note: 
- You may need to run Conda as Admin on  Windows
- Using this method you won't have easy access to the tutorials directly.
  However, you can simply download them manually from [github](https://github.com/oceantracker/oceantracker/tree/ed3186156d5cfe9b7b2c7c15452c7c25be5ceae9/tutorials_how_to)

Please reach out, either via mail or by writing a github issue, if you are running into bugs. We'd be happy to fix them.

## Install by building from source

This is recommended if you plan on working with OceanTracker more extensively or if you are already familiar with python development environments.

```bash
# Navigate to a directory of your choice
cd /path/to/your/directory

# Clone or download the repository
git clone https://github.com/oceantracker/oceantracker.git
cd oceantracker

# Create and activate the environment
mamba env create -f environment.yml
mamba activate oceantracker

# Or if you plan to contribute the development of oceantracker
mamba env create -f environment-deps.yml
mamba activate oceantracker
```

You can also create your own environment as before by
```
cd /path/to/your/directory

# Clone or download the repository
git clone https://github.com/oceantracker/oceantracker.git
cd oceantracker

mamba create -n name_of_your_environment python=3.12
mamba activate -n name_of_your_environment

pip install -e .
# or
# pip install -e .[dev]
```

## Initial test runs

To check that everything runs as intended at this stage you can test your installation by launching your python shell

```bash
python
```

Check that you are using the correct python environment
```python
import sys
print(sys.executable)
```

and then try to spin up OceanTracker

```python
import oceantracker
print(f"OceanTracker version: {oceantracker.__version__}")
```

##########################
Installing
##########################

Requirements
=======================

    Python version >= 3.7

    .. literalinclude:: ../../../requirements.txt
        :language: console
        :caption:

Linux
=======================

Notes: may need to install
    * git
    * python3 pip
    * pip  eg  sudo apt install python3-pip
    * python3-venv, eg sudo  apt install python3.10-venv

before this, eg  sudo apt install python3-pip


#.  Clone repository

    ``git clone https://github.com/oceantracker/oceantracker.git``

#. Working in a Virtual environment
    Change dir to repository dir eg. oceantracker

#. Create virtual environment

    ``python3 -m venv venv``

#. Activate venv

    ``source ./venv/bin/activate``

#. Install packages in venv

    ``python setup.py develop``

    ``pip install -r ./requirements.txt``

#. Test by running a demo

    ``cd ./demos``

    ``python run_demos.py -n --d 2``

#. Deactivate environment

    ``deactivate``

or use command  ``bash linux_install.sh``  with script found in  install folder

.. literalinclude:: ../../../installing/linux_install.sh
    :language: console
    :caption:

Windows
=======================

To create a Conda virtual environment

#. Install Anaconda, then

#. From within folder/dir where oceantracker is to be installed, clone repository

    ``git clone https://github.com/oceantracker/oceantracker.git``

#. Open Andconda command prompt as administrator


#. Create virtual environment

    ``conda env create --file environment.yml``


#. Activate virtual environment

    ``conda activate oceantracker``

#. For Pycharm users,
    # oceantracker should be one of the available Python interpreters so just select it (if it sits within Anaconda3\envs dir),
    # otherwise  add virtual environment manually,  settings/project/interpreter add conda env by navigating to python.exe on dir
    # if  working in folder outside of ocean tracker will ad access with   settings/project/project structure. add root source

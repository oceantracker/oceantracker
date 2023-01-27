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

#. change directorty to oceantracker folder with environment.yml

    ``conda create -n oceantracker``

#. Create virtual environment

    ``conda env create -f environment.yml``

#. Acivate virtual environment

    ``conda acivate oceantracker``

#. For Pycharm users, oceantracker should be one of the available Python interpreters so just select it. If not added it via settings/project/interpreter

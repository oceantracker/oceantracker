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

Create a Conda virtual environment

#.  Install Anaconda for all users (may require admin rights), then change to dir where oceantracker files will reside eg

    ``cd  code/mycodedir``



#. Ensure git is installed, then clone repository

    ``git clone https://github.com/oceantracker/oceantracker.git``

#. Change dir to that with oceantracker

    ``cd ./oceantracker``


#. From within folder/dir where oceantracker is to be installed, clone repository

    ``git clone https://github.com/oceantracker/oceantracker.git``

#. Open Anaconda command prompt as administrator  (may require admin rights), then create virtual environment with file oceantracker/environment.yml

    ``conda env create --file environment.yml``


#. Activate the conda virtual environment

    ``conda activate oceantracker``

#. install oceantracker to be accessible from other dir

    ``pip install --no-deps -e .``



Ways to Run
__________________________

see Running ocean tracker at  :ref:`running-oceantracker`.

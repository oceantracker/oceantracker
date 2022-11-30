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

.. literalinclude:: ../../../tests/oceantracker_linux_install.sh
    :language: console
    :caption:

Windows
=======================

To create a Vonda virtual environment

#. Install Anaconda, then

#. From within folder/dir where oceantracker is to be installed, clone repository

    ``git clone https://github.com/oceantracker/oceantracker.git``

#. Open adaconda command prompt as administrator

#. Create a conda virtual environment

    ``conda create -n oceantracker``

#. Activate virtual environment

    ``conda activate oceantracker``

#. From within   directory containing  oceantracker install dir

    ``conda install --yes --file oceantracker\requirements.txt``

#. To make oceantracker accessible to running code, do one of

        * to use in environment within Pycharm etc  ( in Pycharm, need to add env. to those available from existing conda env., and add oceantracker as source root code)

        * to make accessible to the virtual environment, from within the folder with oceantracker (which has setup.py file), run

                ``python setup.py install``

            or for developers

                ``python setup.py develop``
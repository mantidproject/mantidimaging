Setting up
==========

Obtaining the package
---------------------

A copy of the :code:`mantidimaging` package can be obtained by either cloning
the Git repository:

:code:`git clone https://github.com/mantidproject/mantidimaging.git`

Or downloading a Zip archive of the repository contents:

:code:`wget https://github.com/mantidproject/mantidimaging/archive/master.zip`
:code:`unzip mantidimaging-master.zip`

Setting up Python environment
-----------------------------

Scripts are provided in the :code:`mantidimaging/buildscripts` directory which
setup an Anaconda Python environment which allows you to run the imaging tools.

There are scripts for both Python version 2.7 or version 3.5, if unsure which
version to choose use version 2.7.

Near the end of the Anaconda installation you will be prompted if you wish to
add Anaconda to your PATH in your :code:`.bashrc` file. Be sure to specify
:code:`yes` at this point, this will ensure that the correct version of Python
will be used when launching the package tools.

Installing the package
----------------------

The package can be installed using the following command inside the
:code:`mantidimaging` directory:

:code:`setup.py install`

Alternatively, it can be useful to install via :code:`pip` if you plan on
frequently updating or modifying the package:

:code:`pip install -e .`

Starting the package
--------------------

Once the package is installed it can be launched via either of the following
commands:

    - Command line: :code:`mantidimaging.sh <args...>`
    - iPython: :code:`mantidimaging-ipython.sh <args...>`
    - GUI: :code:`mantidimaging-gui.sh <args...>`

Note that if using Python version 3.5 you will have to activate the virtual
environment before calling any of the above commands. This is done using the
command :code:`source activate py35`. Once finished the command :code:`source
deactivate` can be used to exit the virtual environment.

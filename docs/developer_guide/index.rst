Developer Guide
===============

Getting Started
---------------

You will need conda/mamba, CUDA and gcc installed, see the :ref:`Installation` instructions.

First download the Mantid Imaging source code using Git.

:code:`git clone https://github.com/mantidproject/mantidimaging.git`

If you have a github account you can use ssh access:

:code:`git clone git@github.com:mantidproject/mantidimaging.git`

To set up a developer environment, from with in the cloned directory run:

:code:`python3 ./setup.py create_dev_env`

This will create a conda environment containing all the packages needed to run and develop Mantid Imaging. The activate command will activate the environment.

Afterwards the environment can be activated by running:

:code:`conda activate mantidimaging-dev`

To check that the set up was successful, try running the tests from the source directory:

:code:`python3 -m pytest`

Mantid Imaging can be run directly from the checked-out git directory:

:code:`python3 -m mantidimaging`

or to run with additional diagnostics:

:code:`python3 -X faulthandler -m mantidimaging --log-level DEBUG`


Command Line Arguments
----------------------

- :code:`--log-level` - Set the log verbosity level. Available options are: TRACE, DEBUG, INFO, WARN, CRITICAL
- :code:`--version` - Print the version number and exit.
- :code:`--path` - Set the path for the data you wish to load.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   documentation
   developer_conventions
   conda_packaging_and_docker_image
   release
   testing

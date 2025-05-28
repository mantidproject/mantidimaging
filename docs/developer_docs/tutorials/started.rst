Getting Started
---------------

You will need conda/mamba and CUDA installed, see the :ref:`Installation` instructions. If you are a Linux user, you will also need to complete step 6 of the installation instructions.

*Note that the Python commands given below are for Linux only. To run the commands on Windows, replace* :code:`python3` *with* :code:`python`.

First download the Mantid Imaging source code using Git::

    git clone https://github.com/mantidproject/mantidimaging.git

If you have a github account you can use ssh access (See `Github docs <https://docs.github.com/en/authentication/connecting-to-github-with-ssh>`_ for details)::

    git clone git@github.com:mantidproject/mantidimaging.git

To set up a developer environment, from with in the cloned directory run::

    python3 ./setup.py create_dev_env

This will create a conda environment containing all the packages needed to run and develop Mantid Imaging. The activate command will activate the environment.

Afterwards the environment can be activated by running::

    mamba activate mantidimaging-dev

To check that the set up was successful, try running the tests from the source directory::

    python3 -m pytest

Mantid Imaging can be run directly from the checked-out git directory::

    python3 -m mantidimaging

or to run with additional diagnostics::

    python3 -X faulthandler -m mantidimaging --log-level DEBUG

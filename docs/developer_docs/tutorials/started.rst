.. _getting-started:

Getting Started
---------------

You will need conda/mamba and CUDA installed, see the :ref:`Installation` instructions. If you are a Linux user, you will also need to complete step 6 of the installation instructions.

*Note that the Python commands given below are for Linux only. To run the commands on Windows, replace* :code:`python3` *with* :code:`python`.

First download the Mantid Imaging source code using Git::

    git clone https://github.com/mantidproject/mantidimaging.git

If you have a github account you can use ssh access (See `Github docs <https://docs.github.com/en/authentication/connecting-to-github-with-ssh>`_ for details)::

    git clone git@github.com:mantidproject/mantidimaging.git

To set up a developer environment, from with in the cloned directory run::

    pixi install -e dev

This will create a Pixi environment containing all the packages needed to run and develop Mantid Imaging. The shell command will activate the environment.

Afterwards the environment can be activated by running::

    pixi shell -e dev

To check that the set up was successful, try running the tests from the source directory::

    pixi run test-base

Mantid Imaging can be run directly from the checked-out git directory::

    pixi run MI-gpu

or to run with additional diagnostics::

    pixi run MI-debug-gpu

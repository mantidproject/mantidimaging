Installation
============

Installing
----------

The simplest way to install the toolkit is via Anaconda Cloud, this can be done
with an existing Amaconda or Miniconda distribution if you already have one on
your machine.

1. Download and install `Miniconda 3 <https://conda.io/miniconda.html>`_
2. Create a Python 3.5 virtual environment: :code:`conda create --name mantidimaging python=3.5`
3. Activate the newly created environment: :code:`conda activate mantidimaging`
4. Install mantidimaging: :code:`conda install -c conda-forge -c mantid mantidimaging`

Note that the name of the environment used here (`mantidimaging`) is only an
example and can be changed to whatever name you like.

Running
-------

1. Activate the environment created in the installation step: :code:`conda activate mantidimaging`
2. Run using one of the following commands:

  - GUI: :code:`mantidimaging-gui`
  - IPython: :code:`mantidimaging-ipython`
  - Command line (deprecated): :code:`mantidimaging <args...>`

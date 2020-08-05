.. _Installation:

Installation
============
Installing
----------

The simplest way to install the toolkit is via the packages_ published to Anaconda Cloud, this
can be done with an existing Anaconda or Miniconda distribution if you already
have one on your machine.

.. _packages: https://anaconda.org/mantid/mantidimaging/

1. Download and install `Miniconda 3 <https://conda.io/miniconda.html>`_
2. Add needed channels to Anaconda

  - :code:`conda config --prepend channels defaults`
  - :code:`conda config --prepend channels conda-forge`

3. Make sure the channel priority is flexible

  - :code:`conda config --set channel_priority flexible`

4. Create a virtual environment with Mantid Imaging installed: :code:`conda create -n mantidimaging -c mantid mantidimaging python=3.7`
5. Activate the newly created environment: :code:`conda activate mantidimaging`
6. Install additional :code:`pip` dependencies with :code:`pip install deps/pip-requirements.txt` from the source folder.

Running the source
------------------

1. Activate the environment created in the installation step: :code:`conda activate mantidimaging`
2. Run using one of the following commands:

  - From the root of the repository run with :code:`python -m mantidimaging`


Running the package
-------------------

1. Activate the environment created in the installation step: :code:`conda activate mantidimaging`
2. Run using one of the following commands:

  - GUI: :code:`mantidimaging`
  - IPython: :code:`mantidimaging-ipython`

Updating
--------
To update to the latest version of Mantid Imaging run:

:code:`conda activate mantidimaging && conda update mantidimaging`

Reinstalling the environment
----------------------------
To completely delete the Mantid Imaging environment follow these steps:

- :code:`conda deactivate`

  - to exit out of the conda Mantid Imaging environment

- :code:`conda remove -n mantidimaging --all`

  - and press :code:`y` to confirm

- Follow steps 3 and 4 from Installing_.
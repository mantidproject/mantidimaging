Getting Started with Ada
---------------

.. note:: Ada is a remote VM system available to STFC staff and ISIS users.

First, log in to the `Ada platform <https://ada.stfc.ac.uk/>`_
using your STFC email and password. Once logged in, you can select
*New Workspace > IMAT > Tomography Recommended* to create a new workspace.

After the workspace has been created, you will see two windows: one for the
online VS Code editor and the other for the Ada Workspace GUI.

In the online VS Code editor, select the *hamburger menu (top left) > Terminal > New Terminal*,
and download the Mantid Imaging source code using Git::

    git clone https://github.com/mantidproject/mantidimaging.git

Navigate into the cloned repository directory::

    cd mantidimaging

Load the Conda environment setup script by running::

    source /etc/profile.d/conda.sh

For development, it's recommended to create a new environment that includes the
required tools::

    python3 ./setup.py create_dev_env

This will create an environment named ``mantidimaging-dev``.

Then confirm that the ``mantidimaging-dev`` environment appears when you list Conda environments::

    conda env list

Activate it using::

    mamba activate mantidimaging-dev

Mantid Imaging can then be run using the Ada Workspace GUI window. Open a new terminal in your workspace, activate the
``mantidimaging-dev`` Conda environment, and launch Mantid Imaging with the following command::

    python3 -m mantidimaging


The ``--path`` flag can be used to specify a dataset to load at startup. For example, to launch Mantid Imaging with a reconstructed dataset run::

    python3 -m mantidimaging --path /mnt/ceph/auxiliary/tomography/example_data/processed/flower_recon_200/

Getting Started with Ada
---------------

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

Then confirm that the ``mantidimaging`` and ``mantidimaging_nightly`` environments appear when you list Conda environments::

    conda env list

Activate one of the Mantid Imaging environments:

- ``mantidimaging`` — matches the latest release version
- ``mantidimaging_nightly`` — includes the latest updates from the main GitHub branch
::

    mamba activate <preferred-environment>

Mantid Imaging can then be run using the Ada Workspace GUI window. Open a new terminal in your workspace, activate one of the 
Mantid Imaging Conda environments, and launch Mantid Imaging with the following command::

    python3 -m mantidimaging


The ``--path`` flag can be used to specify a dataset to load at startup. For example, to launch Mantid Imaging with a reconstructed dataset run::

    python3 -m mantidimaging --path /mnt/ceph/auxiliary/tomography/example_data/processed/flower_recon_200/

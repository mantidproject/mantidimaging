Packaging
=========

The preferred method of packaging the package is as a Conda package.

This is most likely to be the simplest way to distribute the package;
Anaconda Cloud is the simplest way to obtain dependencies (for instance,
TomoPy).

TL;DR
-----

Building:

   1. :code:`make build-conda-package`

Installing:

   1. :code:`conda install -c file:///tmp/mantidimaging-conda/linux-64 -c conda-forge  mantidimaging`

Building the package
--------------------

Before you go any further make sure you have the build requirements installed.
This can be done via :code:`make install-build-requirements`.

The metadata is in :code:`conda/`, this generates a package based
on the environment and an installation using :code:`setup.py`.

Note that you may have issues if the Conda root directory is on an encrypted
volume, in this case you may use the :code:`--croot` option to set a root
directory that is on a "normal" volume.

Installing the package
----------------------

Before installing the Conda package the channel from which TomoPy will be
installed must be added to the local Conda configuration. This is done with the
command: :code:`conda config --add channels conda-forge`. This only has to be
done once per machine.

The package can be installed from a local build using: :code:`conda install -c
file:///tmp/mantidimaging-conda/linux-64 mantidimaging` (assuming the package is
still in the directory it was built).

Here you are essentially using a directory as a channel, don't try to install
directly from the archive as it will not resolve dependencies.

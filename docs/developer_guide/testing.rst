Testing
=======

Mantid Imaging uses unit tests, static analysis and GUI approval testing

The full test suite can be run using our makefile target.

On Linux, run the following command:

.. code ::

    make check

On Windows, you will need to install a Windows version of GNU Make.
There are a number of options available, so please speak to other developers on the team if you are struggling to find a suitable installation.

Tests are run automatically on pull requests on GitHub using actions, but should also be run during development.
The full suite of unit tests can run very slowly on a Windows machine. We recommend selecting only relevant tests to run locally when developing on Windows.

Pre-commit
----------

Mantid Imaging uses `pre-commit <https://pre-commit.com/>`_ to run pre-commit hooks. This is included in the development
conda environment and can be installed by using `pip install pre-commit`. After installation, you can then install the
hook scripts with `pre-commit install`. Once this has been completed, the hooks should execute with every commit.

Unit testing
------------

Unit tests can be run using `pytest <https://docs.pytest.org/>`_, e.g.

.. code::

    python -m pytest

For options such as running a subset of tests, see `PyTest Docs <https://docs.pytest.org/en/stable/usage.html>`_


Static analysis
---------------

Mantid Imaging uses `mypy <http://mypy-lang.org/>`_, `ruff <https://beta.ruff.rs/docs/>`_ and `yapf <https://github.com/google/yapf>`_ for static analysis and formatting. They are run by :code:`make check`, or can be run individually, e.g. :code:`make mypy`.


GUI screenshot testing
----------------------

Mantid Imaging uses `Applitools Eyes <https://applitools.com/products-eyes/>`_ for GUI approval testing. Screenshots of windows are uploaded and compared to known good baseline images. This is run in the github action on pull requests.

Applitools requires an API key to use, which can be found via the Applitools web interface. On a developer machine this can be passed as an environment variable. E.g.

Linux:

.. code::

    APPLITOOLS_API_KEY=XXXXXXXXXX xvfb-run --auto-servernum pytest -p no:xdist -p no:randomly -p no:repeat -p no:cov mantidimaging/eyes_tests

Windows:

.. code::

    set APPLITOOLS_API_KEY=XXXXXXXXXX&& python -m pytest -p no:xdist -p no:randomly -p no:repeat -p no:cov mantidimaging/eyes_tests


Differences between uploaded and baseline images can be examined and approved or rejected from the Applitools web interface.

To run without a key or to prevent uploads, set ``APPLITOOLS_API_KEY`` to ``local`` and choose a directory to save the screenshots. Note that this does not check for changes, and will always pass. e.g.

Linux:

.. code::

    mkdir /tmp/gui_test
    APPLITOOLS_API_KEY=local APPLITOOLS_IMAGE_DIR=/tmp/gui_test xvfb-run --auto-servernum pytest -p no:xdist -p no:randomly -p no:repeat -p no:cov mantidimaging/eyes_tests

Windows:

In the command below, replace :code:`[path_to_output_directory]` with the path to the directory that you would like to save the screenshots to.

.. code::

    set APPLITOOLS_API_KEY=local&& set APPLITOOLS_IMAGE_DIR=[path_to_output_directory]&& python -m pytest -p no:xdist -p no:randomly -p no:repeat -p no:cov mantidimaging/eyes_tests


GUI system tests
----------------

GUI system tests run work flows in Mantid Imaging in a 'realistic' way, where possible by using QTest methods to emulate mouse and keyboard actions. They use the same data files as the GUI screenshot tests. These take several minutes to run (longer on Windows) and so must be explicitly requested.

.. code::

    pytest -v --run-system-tests

or in virtual X server xvfb-run (Linux only)

.. code::

    xvfb-run --auto-servernum pytest -v --run-system-tests

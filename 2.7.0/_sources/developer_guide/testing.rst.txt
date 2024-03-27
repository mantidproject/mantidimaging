Testing
=======

Mantid Imaging uses unit tests, static analysis and GUI approval testing

The test suite can be run using our makefile target. Note this does not include the system and screenshot tests::

    make check

On Windows, you may need to install a Windows version of GNU Make.::

    mamba install make

Tests are run automatically on pull requests on GitHub using actions, but should also be run during development.
The full suite of unit tests can run very slowly on a Windows machine. We recommend selecting only relevant tests to run locally when developing on Windows.

See the :file:`Makefile` for the underlying commands if you need to run them with other options.

Pre-commit
----------

Mantid Imaging uses `pre-commit <https://pre-commit.com/>`_ to run pre-commit hooks. This must be manually enabled by running::

    pre-commit install

Once this has been completed, the hooks should execute with every commit.

Unit testing
------------

Unit tests can be run using `pytest <https://docs.pytest.org/>`_, e.g.::

    make pytest

For options such as running a subset of tests, see `PyTest Docs <https://docs.pytest.org/en/stable/usage.html>`_


Static analysis
---------------

Mantid Imaging uses `mypy <http://mypy-lang.org/>`_, `ruff <https://beta.ruff.rs/docs/>`_ and `yapf <https://github.com/google/yapf>`_ for static analysis and formatting. They are run by :code:`make check`, or can be run individually, e.g. :code:`make mypy`.


GUI screenshot testing
----------------------

Mantid Imaging uses `Applitools Eyes <https://applitools.com/products-eyes/>`_ for GUI approval testing. Screenshots of windows are uploaded and compared to known good baseline images. This is run in the github action on pull requests.

The tests can be run locally, where the screenshots will be writen to a directory::

    make test-screenshots

See the :file:`Makefile` for the underlying command used. You may want to run it with a specific output directory by changing :code:`APPLITOOLS_IMAGE_DIR`, or to upload to the Applitools API by setting a :code:`APPLITOOLS_API_KEY` (can be found in the Applitools web interface).


When these tests are run from the automated tests differences between uploaded and baseline images can be examined and approved or rejected from the Applitools web interface.


GUI system tests
----------------

GUI system tests run work flows in Mantid Imaging in a 'realistic' way, where possible by using QTest methods to emulate mouse and keyboard actions. They use the same data files as the GUI screenshot tests. These take several minutes to run (longer on Windows) and so must be explicitly requested.::

    make test-system


Logging
-------

Logging can be controlled using the QSettings configuration file :file:`.config/mantidproject/Mantid Imaging.conf` on Linux or the equivalent registry keys on windows (See `QSettings <https://doc.qt.io/qtforpython-5/PySide2/QtCore/QSettings.html>`_). For example::

    [logging]
    log_level=DEBUG
    log_dir=/tmp/mantid_imaging_logs
    performance_log=true

Benchmarking and profiling
--------------------------

Mantid imaging has some utilities to help with benchmarking and profiling.

The context managers :py:class:`~mantidimaging.core.utility.execution_timer.ExecutionTimer` and :py:class:`~mantidimaging.core.utility.execution_timer.ExecutionProfiler` can be used to wrap some lines of code to record and log its run time. For example::

    with ExecutionProfiler(msg="a_slow_function()"):
        a_slow_function()

will record and log a profile of function calls and times within :code:`a_slow_function()`.

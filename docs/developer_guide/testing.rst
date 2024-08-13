Testing
=======

Mantid Imaging uses a combination of unit tests, static analysis, and GUI approval testing to maintain the stability and quality of the codebase.

The basic test suite, which includes unit tests and static analysis, can be run using our Makefile target. Note that this command does not include the system and screenshot tests::

    make check

On Windows, you may need to install a Windows version of GNU Make::

    mamba install make

Tests are run automatically on pull requests via GitHub Actions, but should also be run locally during development to catch issues early. The full suite of unit tests can run very slowly on a Windows machine, so we recommend selecting only the relevant tests to run locally during development.

For more targeted testing, Mantid Imaging provides several specific commands:

- :code:`make test` : Runs the basic unit test suite to ensure that all unit tests pass. This is ideal after making code changes to confirm that nothing is broken.
- :code:`make test-verbose` : Executes the unit test suite with verbose output, providing detailed information about each test. Useful for gaining more insight when debugging test failures.
- :code:`make test-system` : Runs the system tests, which are typically end-to-end tests that validate the overall functionality of the system. This is particularly useful for confirming that the entire system functions correctly after major updates.

Refer to the :file:`Makefile` for additional options or to modify these commands for specific scenarios.

Pre-commit
----------

Mantid Imaging uses `pre-commit <https://pre-commit.com/>`_ to run pre-commit hooks, ensuring code quality and consistency before changes are committed. These hooks include tasks such as linting, type checks, and formatting.

To enable pre-commit hooks, you must manually install them by running::

    pre-commit install

Once installed, the hooks will execute automatically with every commit.

If you want to run all pre-commit hooks on the entire codebase at once, you can use the following command::

    pre-commit run --all-files

This command executes all pre-commit hooks across the entire codebase, including linting, type checks, and formatting, ensuring that the code meets all quality standards before committing.

Unit testing
------------

Unit tests can be run using `pytest <https://docs.pytest.org/>`_, e.g.::

    make pytest

For options such as running a subset of tests, see `PyTest Docs <https://docs.pytest.org/en/stable/usage.html>`_


Static analysis
---------------

Mantid Imaging uses several tools to ensure high code quality and consistency:

- :code:`mypy <http://mypy-lang.org/>`: Enforces type correctness to catch potential type errors early.
- :code:`ruff <https://beta.ruff.rs/docs/>`: Checks for common syntax and style issues to maintain clean, readable code.
- :code:`yapf <https://github.com/google/yapf>`: Formats code according to PEP 8 standards, ensuring consistent style.

These tools can be run collectively with:

- :code:`make check`: Runs all static analysis tools together for a comprehensive check.

Or individually for specific tasks:

- :code:`make mypy`: Perform static type checks.
- :code:`make ruff`: Lint the code for syntax and style issues.
- :code:`make yapf`: Automatically format code according to PEP 8.


GUI Screenshot Testing
----------------------

Mantid Imaging uses `Applitools Eyes <https://applitools.com/products-eyes/>`_ for GUI approval testing. During this process, screenshots of application windows are captured and compared against known good baseline images to detect any unintended visual changes. This process is integrated into the GitHub Actions workflow and runs automatically on pull requests.

The tests can also be run locally, with options tailored for different platforms:

- **Cross-Platform Testing**: Run the tests on any platform and save the screenshots to a specified directory:

      make test-screenshots

  By default, screenshots are saved to a predefined directory. You can customize the output directory by setting the :code:`APPLITOOLS_IMAGE_DIR` environment variable. For example:

      export APPLITOOLS_IMAGE_DIR=/path/to/your/directory

- **Windows-Specific Testing**: For running screenshot tests specifically on Windows, use the following command:

      make test-screenshots-win

  This command ensures that the graphical output is consistent on Windows, accounting for any platform-specific rendering differences.

If you want to upload the screenshots to the Applitools API for comparison with baseline images stored on their servers, you need to set the :code:`APPLITOOLS_API_KEY` environment variable, which can be obtained from the Applitools web interface:

    export APPLITOOLS_API_KEY=your_applitools_api_key


When these tests are run, either locally or through automated CI, any differences between the newly captured screenshots and the baseline images will be flagged. These differences can be reviewed in the Applitools web interface, where you can approve or reject them based on whether they represent acceptable changes or regressions in the UI.

For more details on the underlying commands and options, refer to the :file:`Makefile`. This will help you customize how the screenshot tests are executed and managed within your development environment.


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

These tools are particularly useful when you need to:

- Optimize performance-critical sections of code.
- Identify bottlenecks in your application.
- Diagnose slow-running functions or processes.

The context managers :py:class:`~mantidimaging.core.utility.execution_timer.ExecutionTimer` and :py:class:`~mantidimaging.core.utility.execution_timer.ExecutionProfiler` can be used to wrap some lines of code to record and log its run time.

To profile a function and log the time spent in each function call, you can use `ExecutionProfiler`::

    with ExecutionProfiler(msg="a_slow_function()"):
        a_slow_function()

will record and log a profile of function calls and times within :code:`a_slow_function()`.

Alternatively, to benchmark the execution time of a specific block of code, use `ExecutionTimer`::

    with ExecutionTimer(msg="a_block_of_code"):
        # Code block to benchmark
        result = some_function()

This will log the total time taken by the code block to execute.

The logged results from `ExecutionTimer` and `ExecutionProfiler` are typically written to the console or a log file, depending on your logging configuration. These logs provide detailed insights into the performance of the profiled code, helping you identify potential bottlenecks.



Debugging
=========

This pages contains some Mantid Imaging specific debugging tips.

Getting Debug Output
--------------------

There are several options that can be used so that Mantid Imaging outputs more information as it runs, for example::

  python -X faulthandler -W default -m mantidimaging --log-level DEBUG

These options:

* Enable the :py:mod:`faulthandler` to dump a traceback in the event of python crash.
* Cause python :py:mod:`warnings` to be printed.
* Set the Mantid Imaging :py:mod:`log level <logging>` to DEBUG.

Logs are written using the Python :py:mod:`logging` module. Mantid Imaging files should access the logger using::

  from logging import getLogger
  ...
  LOG = getLogger(__name__)

and then output using::

  LOG.debug(f'Loaded metadata from: {metadata_filename}')

To avoid large amounts of output, logging messages should only be merged if they are likely to be useful for general debugging.

Debugging Github Actions
------------------------

When errors happen on Github actions it is best to try to reproduce them locally. When that is not possible it may be required to debug them by creating runs by adding commits to a test pull request. In messy cases, it can be best to create a clone of the mantid imaging repository into your Github user account. If you are doing this on the main repository, put :code:`DONTMERGE` in the PR title and commit messages to prevent any accidental merging.

It is usually useful to disable any actions that are not relevant to your issue. On your branch you can delete any un-needed workflows::

  git rm .github/workflows/windows.yml ...
  git commit -m "DONTMERGE: disable workflows"

If the failure is in a specific test, pytest can be told to only run those by adding a :code:`-k` option::

  - name: pytest
  timeout-minutes: 10
  shell: bash -l {0}
  run: |
    xvfb-run --auto-servernum python -m pytest --cov --cov-report=xml -n auto -o log_cli=true --ignore=mantidimaging/eyes_tests --durations=10 -k test_parse_metadata_file




In the case of unreliable test failures, it can be useful to repeat part of the workflow. The :code:`if: success() || failure()` means that each step will run even if previous ones have failed::

      - name: GUI Tests System 1
        if: success() || failure()
        shell: bash -l {0}
        run: |
          xvfb-run --auto-servernum /bin/time -v python -m pytest -vs -rs -p no:xdist -p no:randomly -p no:repeat -p no:cov -o log_cli=true --run-system-tests --durations=10
        timeout-minutes: 30

      - name: GUI Tests System 2
        if: success() || failure()
        shell: bash -l {0}
        run: |
          xvfb-run --auto-servernum /bin/time -v python -m pytest -vs -rs -p no:xdist -p no:randomly -p no:repeat -p no:cov -o log_cli=true --run-system-tests --durations=10
        timeout-minutes: 30

See `Status check functions <https://docs.github.com/en/actions/learn-github-actions/expressions#status-check-functions>`_ for details.

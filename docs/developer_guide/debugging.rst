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

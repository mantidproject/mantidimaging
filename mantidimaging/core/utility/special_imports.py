"""
A place for special import logic to live.

If something requires additional logic to import it for whatever reason (e.g.
version dependencies), it should go in here.
"""

from __future__ import absolute_import, division, print_function

import sys


def import_skimage_io():
    """
    To import skimage io only when it is/can be used
    """
    try:
        from skimage import io as skio
        # tifffile works better on local, but not available on scarf
        # no plugin will use the default python imaging library (PIL)
        # This behaviour might need to be changed when switching to python 3
        skio.use_plugin('tifffile')
    except ImportError as exc:
        raise ImportError(
            "Could not find the package skimage, its subpackage "
            "io and the pluging freeimage which are required to support "
            "several image formats. Error details: {0}".format(exc))
    return skio


def import_mock():
    """
    Loads a suitable version of mock depedning on the Python version being
    used.
    """
    if sys.version_info >= (3, 3):
        # Use unittest.mock on Python 3.3 and above
        import unittest
        import unittest.mock as mock

        if sys.version_info < (3, 6):
            # If on Python 3.5 and below then need to monkey patch this
            # function in It is available as standard on Python 3.6 and above
            def assert_called_once(_mock_self):
                self = _mock_self
                if not self.call_count == 1:
                    msg = ("Expected '{}' to have been called once. "
                           "Called {} times.".format(
                               self._mock_name or 'mock', self.call_count))
                    raise AssertionError(msg)

            unittest.mock.Mock.assert_called_once = assert_called_once
    else:
        # Use mock on Python < 3.3
        import mock

    return mock

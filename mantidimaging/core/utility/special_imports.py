# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
A place for special import logic to live.

If something requires additional logic to import it for whatever reason (e.g.
version dependencies), it should go in here.
"""

from logging import getLogger

LOG = getLogger(__name__)


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
        raise ImportError("Could not find the package skimage, its subpackage "
                          "io and the pluging freeimage which are required to support "
                          "several image formats. Error details: {0}".format(exc))
    return skio

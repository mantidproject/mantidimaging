from __future__ import absolute_import, division, print_function

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.tools import importer

OUTLIERS_DARK = 'dark'
OUTLIERS_BRIGHT = 'bright'
_default_radius = 3
_default_mode = OUTLIERS_BRIGHT


def _cli_register(parser):
    parser.add_argument(
        "--outliers",
        required=False,
        type=float,
        help="Pixel difference above which to crop bright pixels.")

    parser.add_argument(
        "--outliers-radius",
        default=_default_radius,
        required=False,
        type=int,
        help="Default: %(default)s. "
        "Radius for the median filter to determine the outlier.")

    parser.add_argument(
        "--outliers-mode",
        default=_default_mode,
        required=False,
        type=str,
        help="Default: %(default)s. "
        "Crop bright or dark pixels.\n"
        "Cropping dark pixels is more expensive. "
        "It will invert the image before and after removing the outliers")

    return parser


def modes():
    return [OUTLIERS_BRIGHT, OUTLIERS_DARK]


def execute(data, diff, radius=_default_radius, mode=_default_mode,
            cores=None):
    """
    Requires tomopy to be available.

    :param data: Input data as a 3D numpy.ndarray

    :param diff: Pixel value difference above which to crop bright pixels

    :param radius: Size of the median filter to apply

    :param mode: Spot brightness to remove.
                 Either 'bright' or 'dark'.

    :param cores: The number of cores that will be used to process the data.

    :return: The processed 3D numpy.ndarray
    """

    if diff and radius and diff > 0 and radius > 0:
        h.pstart("Applying outliers with threshold: {0} and radius {1}".format(
            diff, radius))

        # we flip the histogram horizontally,
        # this makes the darkest pixels the brightest
        if mode == OUTLIERS_DARK:
            np.negative(data, out=data)

        tomopy = importer.do_importing('tomopy')

        data = tomopy.misc.corr.remove_outlier(data, diff, radius, ncore=cores)

        # reverse the inversion
        if mode == OUTLIERS_DARK:
            np.negative(data, out=data)

        h.pstop("Finished outliers step, with pixel data type: {0}.".format(
            data.dtype))

    return data

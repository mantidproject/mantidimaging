from __future__ import absolute_import, division, print_function

import numpy as np

import helper as h
from core.tools import importer

OUTLIERS_DARK = 'dark'
OUTLIERS_BRIGHT = 'bright'
_default_radius = 3
_default_mode = OUTLIERS_BRIGHT


def cli_register(parser):
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


def gui_register(par):
    raise NotImplementedError("GUI doesn't exist yet")


def modes():
    return [OUTLIERS_DARK, OUTLIERS_BRIGHT]


def execute(data,
            value_difference,
            radius=_default_radius,
            mode=_default_mode,
            cores=None):
    """
    Execute the Outliers filter. Requires tomopy to be available.

    :param data: The sample image data as a 3D numpy.ndarray
    :param value_difference: Pixel value difference above which 
                             to crop bright pixels
    :param radius: Which pixels will be clipped: dark, bright or both
    :param cores: The number of cores that will be used to process the data.

    :return: the data after being processed with the filter

    Example command line:
    python main.py -i /some/data --outliers 1
    python main.py -i /some/data --outliers 1 --outliers-radius 4
    """

    if value_difference and radius and value_difference > 0 and radius > 0:
        h.pstart("Applying outliers with threshold: {0} and radius {1}".format(
            value_difference, radius))

        # we flip the histogram horizontally,
        # this makes the darkest pixels the brightest
        if mode == OUTLIERS_DARK:
            np.negative(data, out=data)

        tomopy = importer.do_importing('tomopy')

        data = tomopy.misc.corr.remove_outlier(
            data, value_difference, radius, ncore=cores)

        # reverse the inversion
        if mode == OUTLIERS_DARK:
            np.negative(data, out=data)

        h.pstop("Finished outliers step, with pixel data type: {0}.".format(
            data.dtype))

    return data

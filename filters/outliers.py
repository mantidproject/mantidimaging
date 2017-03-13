from __future__ import (absolute_import, division, print_function)
from helper import Helper


def modes():
    return ['dark', 'bright', 'both']


def execute(data, outliers_threshold, outliers_radius, cores=None, h=None):
    """
    Execute the Outliers filter.

    :param data: The sample image data as a 3D numpy.ndarray
    :param outliers_threshold: The threshold related to the pixel value that will be clipped
    :param outliers_radius: Which pixels will be clipped: dark, bright or both
    :param h: Helper class, if not provided will be initialised with empty constructor

    :return: the data after being processed with the filter
    """
    h = Helper.empty_init() if h is None else h

    if outliers_threshold and outliers_radius and outliers_threshold > 0 and outliers_radius > 0:
        import numpy as np
        h.pstart("Applying outliers with threshold: {0} and radius {1}".format(
            outliers_threshold, outliers_radius))

        from recon.tools import importer
        tomopy = importer.do_importing('tomopy')

        data[:] = tomopy.misc.corr.remove_outlier(
            data, outliers_threshold, outliers_radius, ncore=cores)

        h.pstop("Finished outliers step, with pixel data type: {0}.".format(
            data.dtype))
    else:
        h.tomo_print_note(
            "NOT applying outliers, because no outliers parameters were specified."
        )

    return data

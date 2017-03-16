from __future__ import (absolute_import, division, print_function)
import helper as h


def modes():
    return ['dark', 'bright', 'both']


def execute(data, outliers_threshold, outliers_radius, cores=None):
    """
    Execute the Outliers filter.

    :param data: The sample image data as a 3D numpy.ndarray
    :param outliers_threshold: The threshold related to the pixel value that will be clipped
    :param outliers_radius: Which pixels will be clipped: dark, bright or both

    :return: the data after being processed with the filter
    """

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

    return data

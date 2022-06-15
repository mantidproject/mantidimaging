# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial

import numpy as np
import scipy.ndimage as scipy_ndimage

from mantidimaging.core.data import ImageStack
from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type

OUTLIERS_DARK = 'dark'
OUTLIERS_BRIGHT = 'bright'
_default_radius = 3
_default_mode = OUTLIERS_BRIGHT
DIM_2D = "2D"
DIM_1D = "1D"


class OutliersFilter(BaseFilter):
    """Removes pixel values that are found to be outliers as defined by the given parameters.

    Intended to be used on: Projections

    When: As a pre-processing step to reduce very bright or dead pixels in the data.

    Caution: This should usually be one of the first steps applied to the data, flat and dark
    images, to remove pixels with very large values that will cause issues for flat-fielding.
    """
    filter_name = "Remove Outliers"
    link_histograms = True

    @staticmethod
    def _execute(data, diff, radius, mode):
        # Adapted from tomopy source
        median = scipy_ndimage.median_filter(data, radius)
        if mode == OUTLIERS_BRIGHT:
            return np.where((data - median) > diff, median, data)
        else:
            return np.where((median - data) > diff, median, data)

    @staticmethod
    def filter_func(images: ImageStack,
                    diff=None,
                    radius=_default_radius,
                    mode=_default_mode,
                    progress: Progress = None):
        """
        :param images: Input data
        :param diff: Pixel value difference above which to crop bright pixels
        :param radius: Size of the median filter to apply
        :param mode: Whether to remove bright or dark outliers
                    One of [OUTLIERS_BRIGHT, OUTLIERS_DARK]

        :return: The processed 3D numpy.ndarray
        """
        if not diff or not diff > 0:
            raise ValueError(f'diff parameter must be greater than 0. Value provided was {diff}')

        if not radius or not radius > 0:
            raise ValueError(f'radius parameter must be greater than 0. Value provided was {radius}')

        func = ps.create_partial(OutliersFilter._execute, ps.return_to_self, diff=diff, radius=radius, mode=mode)
        ps.execute(func, [images.shared_array],
                   images.data.shape[0],
                   progress=progress,
                   msg=f"Outliers with threshold {diff} and kernel {radius}")
        return images

    @staticmethod
    def register_gui(form, on_change, view):
        _, diff_field = add_property_to_form('Difference',
                                             'float',
                                             1000,
                                             valid_values=(1e-7, 10000),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Difference between pixels that will be used to spot outliers.\n"
                                             "It is calculated by subtracting the original image "
                                             "from the median filtered image")
        diff_field.setDecimals(7)

        _, size_field = add_property_to_form('Median kernel',
                                             Type.INT,
                                             3, (1, 1000),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="The size of the median filter kernel used to find outliers.")

        _, mode_field = add_property_to_form('Mode',
                                             Type.CHOICE,
                                             valid_values=modes(),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Whether to remove bright or dark outliers")

        return {'diff_field': diff_field, 'size_field': size_field, 'mode_field': mode_field}

    @staticmethod
    def execute_wrapper(diff_field=None, size_field=None, mode_field=None):

        return partial(OutliersFilter.filter_func,
                       diff=diff_field.value(),
                       radius=size_field.value(),
                       mode=mode_field.currentText())

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Basic


def modes():
    return [OUTLIERS_BRIGHT, OUTLIERS_DARK]

from functools import partial

import numpy as np
import scipy.ndimage as scipy_ndimage

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.core.parallel import utility
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type

_default_radius = 3


class OutliersISISFilter(BaseFilter):
    filter_name = "Remove Outliers ISIS"

    @staticmethod
    def _execute(data, diff, radius):
        # Adapted for 2D image from source: https://stackoverflow.com/a/16562028/2823526
        median = scipy_ndimage.median_filter(data, radius)
        abs_diff = np.abs(data - median)
        mdev = np.median(abs_diff)
        s = abs_diff / mdev
        return np.where(s < diff, data, median)

    @staticmethod
    def filter_func(images: Images, diff=None, radius=_default_radius, axis=0, cores=None, progress=None):
        """
        :param images: Input data
        :param diff: Pixel value difference above which to crop bright pixels
        :param radius: Size of the median filter to apply
        :param cores: The number of cores that will be used to process the data.

        :return: The processed 3D numpy.ndarray
        """
        if not utility.multiprocessing_necessary(images.data.shape, cores):
            cores = 1

        if diff and radius and diff > 0 and radius > 0:
            data = images.projections if axis == 0 else images.sinograms
            func = psm.create_partial(OutliersISISFilter._execute, psm.return_fwd_func, diff=diff, radius=radius)
            psm.execute(data, func, cores, progress=progress, msg=f"Outliers with threshold {diff} and kernel {radius}")
        return images

    @staticmethod
    def register_gui(form, on_change, view):
        _, diff_field = add_property_to_form('Difference',
                                             'float',
                                             1,
                                             valid_values=(-1000000, 1000000),
                                             form=form,
                                             on_change=on_change)
        diff_field.setDecimals(7)

        _, size_field = add_property_to_form('Size', Type.INT, 3, (0, 1000), form=form, on_change=on_change)

        _, apply_to_field = add_property_to_form('Apply to',
                                                 Type.CHOICE,
                                                 valid_values=("Projections", "Sinograms"),
                                                 form=form,
                                                 on_change=on_change)

        return {'diff_field': diff_field, 'size_field': size_field, 'apply_to_field': apply_to_field}

    @staticmethod
    def execute_wrapper(diff_field=None, size_field=None, apply_to_field=None):
        if apply_to_field.currentText() == "Projections":
            axis = 0
        elif apply_to_field.currentText() == "Sinograms":
            axis = 1
        else:
            raise AttributeError("apply_to_field not given a valid input.")

        return partial(OutliersISISFilter.filter_func, diff=diff_field.value(), radius=size_field.value(), axis=axis)

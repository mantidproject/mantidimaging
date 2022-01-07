# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from logging import getLogger
import numpy as np

import scipy.ndimage as scipy_ndimage

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type


class GaussianFilter(BaseFilter):
    """Applies Gaussian filter to the data.

    Intended to be used on: Projections or reconstructed slices

    When: As a pre-processing or post-reconstruction step to reduce noise.
    """
    filter_name = "Gaussian"
    link_histograms = True

    @staticmethod
    def filter_func(data: Images, size=None, mode=None, order=None, cores=None, chunksize=None, progress=None):
        """
        :param data: Input data as a 3D numpy.ndarray
        :param size: Size of the kernel
        :param mode: The mode with which to handle the edges.
                     One of [reflect, constant, nearest, mirror, wrap].
                     Modes are described in the `SciPy documentation
                     <https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html>`_.
        :param order: The order of the filter along each axis is given as a
                      sequence of integers, or as a single number.
                      An order of 0 corresponds to convolution with a Gaussian
                      kernel.
                      An order of 1, 2, or 3 corresponds to convolution
                      with the first, second or third derivatives of a Gaussian.
                      Higher order derivatives are not implemented
        :param cores: The number of cores that will be used to process the data.
        :param chunksize: The number of chunks that each worker will receive.

        :return: The processed 3D numpy.ndarray
        """
        h.check_data_stack(data)

        if not size or not size > 1:
            raise ValueError(f'Size parameter must be greater than 1, but value provided was {0}', size)

        _execute(data.data, size, mode, order, cores, progress)
        h.check_data_stack(data)
        return data

    @staticmethod
    def register_gui(form, on_change, view):
        _, size_field = add_property_to_form('Kernel Size',
                                             Type.INT,
                                             3, (2, 1000),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Size of the median filter kernel")

        _, order_field = add_property_to_form('Order',
                                              Type.INT,
                                              0, (0, 3),
                                              form=form,
                                              on_change=on_change,
                                              tooltip="Order of the Gaussian filter")

        _, mode_field = add_property_to_form('Edge Mode',
                                             Type.CHOICE,
                                             valid_values=modes(),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Mode to handle the edges of the image")

        return {'size_field': size_field, 'order_field': order_field, 'mode_field': mode_field}

    @staticmethod
    def execute_wrapper(size_field=None, order_field=None, mode_field=None):
        return partial(GaussianFilter.filter_func,
                       size=size_field.value(),
                       mode=mode_field.currentText(),
                       order=order_field.value())


def modes():
    return ['reflect', 'constant', 'nearest', 'mirror', 'wrap']


def _execute(data: np.ndarray, size, mode, order, cores=None, progress=None):
    log = getLogger(__name__)
    progress = Progress.ensure_instance(progress, task_name='Gaussian filter')

    f = ps.create_partial(scipy_ndimage.gaussian_filter, ps.return_to_self, sigma=size, mode=mode, order=order)

    log.info("Starting PARALLEL gaussian filter, with pixel data type: {0}, "
             "filter size/width: {1}.".format(data.dtype, size))

    progress.update()
    ps.shared_list = [data]
    ps.execute(f, data.shape[0], progress, msg="Gaussian filter", cores=cores)

    progress.mark_complete()
    log.info("Finished  gaussian filter, with pixel data type: {0}, "
             "filter size/width: {1}.".format(data.dtype, size))

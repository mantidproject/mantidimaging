# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from logging import getLogger
from typing import Callable, Any, TYPE_CHECKING

import numpy as np
from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QSpinBox, QLabel, QSizePolicy

import scipy.ndimage as scipy_ndimage

from mantidimaging import helper as h
from mantidimaging.core.gpu import utility as gpu
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type, on_change_and_disable

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout  # pragma: no cover
    from mantidimaging.core.data import ImageStack

KERNEL_SIZE_TOOLTIP = "Size of the median filter kernel"


class KernelSpinBox(QSpinBox):

    def __init__(self, on_change: Callable):
        """
        Spin box for entering kernel sizes that only accepts odd numbers.
        :param on_change: The function to be called when the value changes.
        """
        super().__init__()
        self.setMinimum(3)
        self.setMaximum(999)
        self.setSingleStep(2)
        self.setKeyboardTracking(False)
        self.setToolTip(KERNEL_SIZE_TOOLTIP)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.valueChanged.connect(lambda: on_change_and_disable(self, on_change))

    def validate(self, input: str, pos: int) -> tuple[QValidator.State, str, int]:
        """
        Validate the spin box input. Returns as Intermediate state if the input is empty or contains an even number,
        otherwise it returns Acceptable.
        """
        if not input:
            return QValidator.State.Intermediate, input, pos
        kernel_size = int(input)
        if kernel_size % 2 != 0:
            return QValidator.State.Acceptable, input, pos
        return QValidator.State.Intermediate, input, pos


class MedianFilter(BaseFilter):
    """Applies Median filter to the data.

    Intended to be used on: Projections or reconstructed slices

    When: As a pre-processing or post-reconstruction step to reduce noise.

    Note: NaN values are preserved through the filter. They are treated as negative infinity while calculating
    neighbouring pixels.
    """
    filter_name = "Median"
    link_histograms = True

    @staticmethod
    def filter_func(data: ImageStack, size=None, mode="reflect", progress=None, force_cpu=True):
        """
        :param data: Input data as an ImageStack object.
        :param size: Size of the kernel
        :param mode: The mode with which to handle the edges.
                     One of [reflect, constant, nearest, mirror, wrap].
                     Modes are described in the `SciPy documentation
                     <https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.median_filter.html>`_.
        :param progress: The object for displaying the progress.
        :param force_cpu: Whether or not to use the CPU.

        :return: Returns the processed data

        """
        # Validation
        h.check_data_stack(data)
        if size is None or size <= 1:
            raise ValueError(f'Size parameter must be greater than 1, but value provided was {size}')

        params = {'mode': mode, 'size': size, 'force_cpu': force_cpu, 'progress': progress}
        if force_cpu:
            ps.run_compute_func(MedianFilter.compute_function, data.data.shape[0], data.shared_array, params)
        else:
            _execute_gpu(data.data, size, mode, progress=None)
        return data

    @staticmethod
    def compute_function(i: int, array: np.ndarray, params: dict[str, Any]):
        mode = params['mode']
        size = params['size']

        array[i] = _median_filter(array[i], size=size, mode=mode)

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view) -> dict[str, Any]:

        # Create a spin box for kernel size without add_property_to_form in order to allow a custom validate method
        size_field = KernelSpinBox(on_change)
        size_field_label = QLabel("Kernel Size")
        size_field_label.setToolTip(KERNEL_SIZE_TOOLTIP)
        form.addRow(size_field_label, size_field)

        _, mode_field = add_property_to_form('Edge Mode',
                                             Type.CHOICE,
                                             valid_values=modes(),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Mode to handle the edges of the image")

        _, gpu_field = add_property_to_form('Use GPU',
                                            Type.BOOL,
                                            default_value=False,
                                            tooltip='Run the median filter on the GPU',
                                            form=form,
                                            on_change=on_change)

        return {'size_field': size_field, 'mode_field': mode_field, 'use_gpu_field': gpu_field}

    @staticmethod
    def execute_wrapper(size_field=None, mode_field=None, use_gpu_field=None):
        return partial(MedianFilter.filter_func,
                       size=size_field.value(),
                       mode=mode_field.currentText(),
                       force_cpu=not use_gpu_field.isChecked())


def modes():
    return ['reflect', 'constant', 'nearest', 'mirror', 'wrap']


def _median_filter(data: np.ndarray, size: int, mode: str) -> np.ndarray:
    nans = np.isnan(data)
    data = np.where(nans, -np.inf, data)
    # Put the original NaNs back
    data = scipy_ndimage.median_filter(data, size=size, mode=mode)
    data = np.where(nans, np.nan, data)
    return data


def _execute_gpu(data, size, mode, progress=None):
    log = getLogger(__name__)
    progress = Progress.ensure_instance(progress, num_steps=data.shape[0], task_name="Median filter GPU")
    cuda = gpu.CudaExecuter(data.dtype)

    with progress:
        log.info(f"GPU median filter, with pixel data type: {data.dtype}, filter size/width: {size}.")

        cuda.median_filter(data, size, mode, progress)

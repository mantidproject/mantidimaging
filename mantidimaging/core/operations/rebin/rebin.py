# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numpy as np
from skimage.transform import resize

from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import utility as pu, shared as ps
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


class RebinFilter(BaseFilter):
    """Rebin the image to reduce the resolution.

    This filter temporarily increases memory usage, while the image is being rebinned.
    The memory usage will be lowered after the filter has finished executing.

    Intended to be used on: Any data

    When: If you want to reduce the data size and to smoothen the image.
    """
    filter_name = "Rebin"
    link_histograms = True

    @staticmethod
    def filter_func(images: ImageStack, rebin_param=0.5, mode=None, progress=None) -> ImageStack:
        """
        :param images: Sample data which is to be processed. Expects radiograms
        :param rebin_param: int, float or tuple
                            int - Percentage of current size.
                            float - Fraction of current size.
                            tuple - Size of the output image (x, y).
        :param mode: The mode with which to handle the edges. One of
                     ('constant', 'edge', 'symmetric', 'reflect', 'wrap').

        :return: The processed 3D numpy.ndarray
        """
        if isinstance(rebin_param, tuple):
            new_shape = rebin_param
        elif isinstance(rebin_param, (int | float)):
            current_shape = images.data.shape[1:]
            new_shape = (int(current_shape[0] * rebin_param), int(current_shape[1] * rebin_param))
        else:
            raise ValueError("Invalid type for rebin_param")

        output = _create_reshaped_array(images, rebin_param)

        params = {'new_shape': new_shape, 'mode': mode}
        ps.run_compute_func(RebinFilter.compute_function, images.data.shape[0], [images.shared_array, output], params,
                            progress)
        images.shared_array = output
        return images

    @staticmethod
    def compute_function(i: int, arrays: list[np.ndarray], params: dict):
        array = arrays[0]
        output = arrays[1]
        new_shape = params['new_shape']
        mode = params['mode']
        output[i] = resize(array[i], output_shape=new_shape, mode=mode, preserve_range=True)

    @staticmethod
    def register_gui(form, on_change, view):
        # Rebin by uniform factor options
        _, factor = add_property_to_form('Factor',
                                         'float',
                                         0.5, (0.01, 4.0),
                                         on_change=on_change,
                                         tooltip="Factor by which the data will be rebinned, "
                                         "e.g. 0.5 is 50% reduced size",
                                         single_step_size=0.05)

        # Rebin to target shape options
        shape_range = (1, 9999)

        _, shape_x = add_property_to_form('X', Type.INT, 100, shape_range, on_change=on_change)
        _, shape_y = add_property_to_form('Y', Type.INT, 100, shape_range, on_change=on_change)

        from PyQt5.QtWidgets import QHBoxLayout, QRadioButton, QLabel, QComboBox
        shape_fields = QHBoxLayout()
        shape_fields.addWidget(shape_x)
        shape_fields.addWidget(shape_y)

        # Rebin dimension selection options
        rebin_by_factor_radio = QRadioButton("Rebin by Factor")

        def size_by_factor_toggled(enabled):
            factor.setEnabled(enabled)
            on_change()

        rebin_by_factor_radio.toggled.connect(size_by_factor_toggled)

        rebin_to_dimensions_radio = QRadioButton("Rebin to Dimensions")

        def size_by_dimensions_toggled(enabled):
            shape_x.setEnabled(enabled)
            shape_y.setEnabled(enabled)
            on_change()

        rebin_to_dimensions_radio.toggled.connect(size_by_dimensions_toggled)

        # Rebin mode options
        label_mode = QLabel("Mode")
        mode_field = QComboBox()
        mode_field.addItems(modes())

        form.addRow(rebin_to_dimensions_radio, shape_fields)
        form.addRow(rebin_by_factor_radio, factor)
        form.addRow(label_mode, mode_field)

        # Ensure good default UI state
        rebin_to_dimensions_radio.setChecked(True)
        rebin_by_factor_radio.setChecked(True)

        return {
            "rebin_to_dimensions_radio": rebin_to_dimensions_radio,
            "shape_x": shape_x,
            "shape_y": shape_y,
            "rebin_by_factor_radio": rebin_by_factor_radio,
            "factor": factor,
            "mode_field": mode_field,
        }

    @staticmethod
    def execute_wrapper(rebin_to_dimensions_radio=None,
                        shape_x=None,
                        shape_y=None,
                        rebin_by_factor_radio=None,
                        factor=None,
                        mode_field=None):
        if rebin_to_dimensions_radio.isChecked():
            params = (shape_x.value(), shape_y.value())
        elif rebin_by_factor_radio.isChecked():
            params = factor.value()
        else:
            raise ValueError('Unknown bin dimension mode')

        return partial(RebinFilter.filter_func, mode=mode_field.currentText(), rebin_param=params)


def _create_reshaped_array(images, rebin_param):
    old_shape = images.data.shape
    num_images = old_shape[0]

    # use SciPy's calculation to find the expected dimensions
    # int to avoid visible deprecation warning
    if isinstance(rebin_param, tuple):
        expected_dimy = int(rebin_param[0])
        expected_dimx = int(rebin_param[1])
    else:
        expected_dimy = int(rebin_param * old_shape[1])
        expected_dimx = int(rebin_param * old_shape[2])

    shape = (num_images, expected_dimy, expected_dimx)
    return pu.create_array(shape, images.dtype)


def modes():
    return ["constant", "edge", "wrap", "reflect", "symmetric"]

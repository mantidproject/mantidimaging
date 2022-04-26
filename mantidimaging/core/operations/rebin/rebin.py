# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial

import skimage.transform

from mantidimaging import helper as h
from mantidimaging.core.data import ImageStack
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.parallel import utility as pu
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type


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
        :param mode: Interpolation to use for re-sizing
                     ('nearest', 'lanczos', 'bilinear', 'bicubic' or 'cubic').

        :return: The processed 3D numpy.ndarray
        """
        h.check_data_stack(images)

        if isinstance(rebin_param, tuple):
            param_valid = rebin_param[0] > 0 and rebin_param[1] > 0
        else:
            param_valid = rebin_param > 0

        if not param_valid:
            raise ValueError('Rebin parameter must be greater than 0')

        empty_resized_data = _create_reshaped_array(images, rebin_param)

        f = ps.create_partial(skimage.transform.resize,
                              ps.return_to_second_at_i,
                              mode=mode,
                              output_shape=empty_resized_data.array.shape[1:])
        ps.execute(partial_func=f,
                   arrays=[images.shared_array, empty_resized_data],
                   num_operations=images.data.shape[0],
                   msg="Applying Rebin",
                   progress=progress)
        images.shared_array = empty_resized_data

        return images

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


def modes():
    return ["constant", "edge", "wrap", "reflect", "symmetric"]


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

    # allocate memory for images with new dimensions
    shape = (num_images, expected_dimy, expected_dimx)
    return pu.create_array(shape, images.dtype)

# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING
from skimage.transform import rotate
from PyQt5.QtWidgets import QComboBox

from mantidimaging import helper as h
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.parallel import utility as pu
from mantidimaging.gui.utility.qt_helpers import Type

import numpy as np

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


class RotateFilter(BaseFilter):
    """Rotates the image data by an arbitrary degree counter-clockwise.

    Intended to be used on: Projections

    When: 90 or 270 degree rotation for rotation axis to be vertical for some camera types.

    Caution: Rotations of images others than multiples of 90 degrees could introduce additional
    artifacts in the reconstructed volume. Such rotations are usually not required as
    small tilts can be taken into account at the reconstruction stage.
    """
    filter_name = "Rotate Stack"
    link_histograms = True

    @staticmethod
    def filter_func(data: ImageStack, angle=None, progress=None):
        """
        Rotates images by an arbitrary degree.

        param data: stack of sample images
        param angle: The rotation to be performed, in degrees

        return: The rotated images
        """
        h.check_data_stack(data)
        if angle is None:
            raise ValueError('Value must be provided for angle parameter')
        progress = Progress.ensure_instance(progress, task_name='Rotate Stack')
        _do_rotation(data, round(angle, 3), progress)
        return data

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        dropdown = QComboBox()
        dropdown.addItems(['90', '180', '270', 'Custom'])
        _, dropdown = add_property_to_form('Angle presets (degrees)',
                                           Type.CHOICE,
                                           0, ('0', '90', '180', '270', "Custom"),
                                           form=form,
                                           on_change=on_change,
                                           tooltip="How much degrees to rotate counter-clockwise")

        _, angle = add_property_to_form('Custom Angle of rotation\ncounter clockwise (degrees)',
                                        Type.FLOAT,
                                        0, (-359, 359),
                                        form=form,
                                        on_change=on_change,
                                        tooltip="How much degrees to rotate counter-clockwise")
        angle.setDecimals(3)
        angle.setEnabled(False)
        dropdown.currentTextChanged.connect(lambda text: RotateFilter._update_angle(angle, dropdown))
        return {"angle": angle}

    @staticmethod
    def execute_wrapper(angle=None):
        return partial(RotateFilter.filter_func, angle=angle.value())

    @staticmethod
    def _update_angle(angle, dropdown):
        """
        Handle Dropdown change event to set value is angle is not custom

        :param angle: angle widget
        :param dropdown: dropdown widget
        """
        if dropdown.currentText() == 'Custom':
            angle.setEnabled(True)
        else:
            angle.setValue(float(dropdown.currentText()))
            angle.setEnabled(False)


def _get_cardinal_angle(general_angle) -> int:
    """
    Calculates the cardinal angle based on the general input angle by rounding to
    the nearest 90 degree and then mod 360. Ths is used to determine if the angle
    is a cardinal angle or not and also return a cardinal angle for in-place rotations.

    param: value: general angle of rotation
    return: angle: cardinal angle of rotation
    """
    return (round(general_angle / 90) * 90) % 360


def _do_rotation(data, angle, progress) -> np.ndarray:
    """
    Handle rotation of image slice by angle. This includes rotation of aspect
    ratio and in place rotation depending on angle.

    param array_index: index of array in array_list
    param data: current image data array
    param angle: angle of rotation
    return: new_data: rotated image data array
    """
    angle = angle % 360
    if angle == _get_cardinal_angle(angle):
        data.shared_array = _cardinal_rotation_per_slice(data, angle, progress)
    else:
        data.shared_array = _cardinal_rotation_per_slice(data, _get_cardinal_angle(angle), progress)
        data.shared_array = _inplace_rotation(data.data.shape[0], data, angle - _get_cardinal_angle(angle), progress)
    return data


def _cardinal_rotation_per_slice(data: ImageStack, angle: float, progress) -> pu.SharedArray:
    """
    Perform a cardinal rotation of the image stack by angle if angle is cardinal and additionally
    in-place rotation if general angle.

    param: data: current image data array
    param: angle: angle of rotation
    param: progress: progress bar
    return: new_data: rotated image data array
    """
    z_axis, y_axis, x_axis = data.data.shape
    rotated_shape: tuple = (z_axis, x_axis, y_axis)

    if angle == 0 or angle == 180:
        new_data = _inplace_rotation(z_axis, data, angle, progress)
    else:
        new_data = pu.create_array(rotated_shape, data.data.dtype)
        ps.run_compute_func(_compute_cardinal_rotation_per_slice, z_axis, [data.shared_array, new_data],
                            {"angle": angle}, progress)
    return new_data


def _inplace_rotation(number_of_slices: int, data, angle: float, progress) -> pu.SharedArray:
    """
    In-place rotation of image slices by angle.

    param: number_of_slices: array slices
    param: data: current image data array
    param: angle: angle of rotation
    param: progress: progress bar
    return: new_data: rotated image data array
    """
    ps.run_compute_func(_compute_rotation_per_slice_inplace, number_of_slices, data.shared_array, {"angle": angle},
                        progress)
    return data.shared_array


def _compute_cardinal_rotation_per_slice(array_index, array_list, angle):
    """
    Rotate array in increments of 90 degrees.
    param: array_index: index of array in array_list
    param: array_list: list of arrays - [old_array, new_array]
    param: angle: angle of rotation
    """
    cardinal_rotation = {0: 0, 90: 1, 180: 2, 270: 3}
    array_list[1][array_index] = np.rot90(array_list[0][array_index], k=cardinal_rotation[angle["angle"]])


def _compute_rotation_per_slice_inplace(array_index, array_list, angle):
    """
    Rotate array in-place so that aspect ratio is not changed
    param: array_list: list of arrays - [array]
    param: angle: angle of rotation
    """
    array_list[array_index] = rotate(array_list[array_index], angle["angle"])

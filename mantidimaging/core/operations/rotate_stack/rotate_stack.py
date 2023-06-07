# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
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
from mantidimaging.gui.utility.qt_helpers import Type

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

        :param data: stack of sample images
        :param angle: The rotation to be performed, in degrees

        :return: The rotated images
        """
        h.check_data_stack(data)

        if angle is None:
            raise ValueError('Value must be provided for angle parameter')

        # No need to run the filter for an angle of 0 as it won't have any effect
        if not angle == 0:
            _execute(data, angle, progress)

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
        angle.setDecimals(7)
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
        dropdown_angle = dropdown.currentText()
        if dropdown_angle == 'Custom':
            angle.setEnabled(True)
        else:
            angle.setValue(float(dropdown_angle))
            angle.setEnabled(False)


def _rotate_image_inplace(data, angle=None):
    data[:, :] = rotate(data[:, :], angle)


def _execute(images: ImageStack, angle: float, progress: Progress):
    progress = Progress.ensure_instance(progress, task_name='Rotate Stack')

    with progress:
        f = ps.create_partial(_rotate_image_inplace, ps.inplace1, angle=angle)
        ps.execute(f, [images.shared_array], images.data.shape[0], progress, msg=f"Rotating by {angle} degrees")

    return images

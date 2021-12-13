# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import numpy as np
import traceback
from enum import IntEnum, auto
from logging import getLogger
from typing import TYPE_CHECKING

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import const
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.mvp_base import BasePresenter
from .model import SVModel
from ...utility.common import operation_in_progress

if TYPE_CHECKING:
    from .view import StackVisualiserView  # pragma: no cover


class SVNotification(IntEnum):
    REFRESH_IMAGE = auto()
    TOGGLE_IMAGE_MODE = auto()
    SWAP_AXES = auto()
    DUPE_STACK = auto()
    DUPE_STACK_ROI = auto()


class SVParameters(IntEnum):
    """
    Stack Visualiser parameters that the Stack Visualiser presenter can retrieve
    """
    ROI = 0


class SVImageMode(IntEnum):
    NORMAL = 0
    SUMMED = 1


class StackVisualiserPresenter(BasePresenter):
    view: 'StackVisualiserView'

    def __init__(self, view: 'StackVisualiserView', images: Images):
        super().__init__(view)
        self.model = SVModel()
        self.images = images
        self._current_image_index = 0
        self.image_mode: SVImageMode = SVImageMode.NORMAL
        self.summed_image = None

    def notify(self, signal):
        try:
            if signal == SVNotification.REFRESH_IMAGE:
                self.refresh_image()
            elif signal == SVNotification.TOGGLE_IMAGE_MODE:
                self.toggle_image_mode()
            elif signal == SVNotification.SWAP_AXES:
                self.create_swapped_axis_stack()
            elif signal == SVNotification.DUPE_STACK:
                self.dupe_stack()
            elif signal == SVNotification.DUPE_STACK_ROI:
                self.dupe_stack_roi()
        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def delete_data(self):
        self.images = None

    def get_image(self, index) -> Images:
        return self.images.index_as_images(index)

    def refresh_image(self):
        self.view.image = self.summed_image if self.image_mode is SVImageMode.SUMMED \
            else self.images.data

    def get_parameter_value(self, parameter: SVParameters):
        """
        Gets a parameter from the stack visualiser for use elsewhere (e.g. operations).
        :param parameter: The parameter value to be retrieved
        """
        if parameter == SVParameters.ROI:
            return self.view.current_roi
        else:
            raise ValueError("Invalid parameter name has been requested from the Stack "
                             "Visualiser, parameter: {0}".format(parameter))

    def toggle_image_mode(self):
        if self.image_mode is SVImageMode.NORMAL:
            self.image_mode = SVImageMode.SUMMED
        else:
            self.image_mode = SVImageMode.NORMAL

        if self.image_mode is SVImageMode.SUMMED and \
                (self.summed_image is None
                 or self.summed_image.shape != self.images.data.shape[1:]):
            self.summed_image = self.model.sum_images(self.images.data)
        self.refresh_image()

    def create_swapped_axis_stack(self):
        with operation_in_progress("Creating sinograms, copying data, this may take a while",
                                   "The data is being copied, this may take a while.", self.view):
            new_stack = self.images.copy(flip_axes=True)
            new_stack.record_operation(const.OPERATION_NAME_AXES_SWAP, display_name="Axes Swapped")
            self.view.parent_create_stack(new_stack, f"{self.view.name}_sino")

    def dupe_stack(self):
        with operation_in_progress("Copying data, this may take a while",
                                   "The data is being copied, this may take a while.", self.view):
            new_images = self.images.copy(flip_axes=False)
            self.view.parent_create_stack(new_images, self.view.name)

    def dupe_stack_roi(self):
        with operation_in_progress("Copying data, this may take a while",
                                   "The data is being copied, this may take a while.", self.view):
            new_images = self.images.copy_roi(SensibleROI.from_points(*self.view.image_view.get_roi()))
            self.view.parent_create_stack(new_images, self.view.name)

    def get_num_images(self) -> int:
        return self.images.num_projections

    def find_image_from_angle(self, selected_angle: float) -> int:
        selected_angle = np.deg2rad(selected_angle)
        for index, angle in enumerate(self.images.projection_angles().value):
            if angle >= selected_angle:
                return index
        return len(self.images.projection_angles().value)

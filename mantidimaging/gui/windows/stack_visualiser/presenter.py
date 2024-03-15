# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
import traceback
from enum import IntEnum, auto
from logging import getLogger
from typing import TYPE_CHECKING

from mantidimaging.core.data import ImageStack
from mantidimaging.core.operation_history import const
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.mvp_base import BasePresenter
from .model import SVModel
from ...utility.common import operation_in_progress
from mantidimaging.core.data.dataset import MixedDataset

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
    view: StackVisualiserView

    def __init__(self, view: StackVisualiserView, images: ImageStack):
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
        self.view.cleanup()
        self.view = None

    def refresh_image(self):
        if self.image_mode is SVImageMode.SUMMED:
            self.view.image = self.summed_image
        else:
            self.view.set_image(self.images)

    def get_parameter_value(self, parameter: SVParameters):
        """
        Gets a parameter from the stack visualiser for use elsewhere (e.g. operations).
        :param parameter: The parameter value to be retrieved
        """
        if parameter == SVParameters.ROI:
            return self.view.current_roi
        else:
            raise ValueError("Invalid parameter name has been requested from the Stack "
                             f"Visualiser, parameter: {parameter}")

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
            new_stack.name = self.images.name + "_sino"
            new_stack.record_operation(const.OPERATION_NAME_AXES_SWAP, display_name="Axes Swapped")
            self.add_sinograms_to_model_and_update_view(new_stack)

    def dupe_stack(self):
        with operation_in_progress("Copying data, this may take a while",
                                   "The data is being copied, this may take a while.", self.view):
            new_images = self.images.copy(flip_axes=False)
            new_images.name = self.images.name
            self.add_mixed_dataset_to_model_and_update_view(new_images)

    def dupe_stack_roi(self):
        with operation_in_progress("Copying data, this may take a while",
                                   "The data is being copied, this may take a while.", self.view):
            new_images = self.images.copy_roi(SensibleROI.from_points(*self.view.image_view.get_roi()))
            new_images.name = self.images.name
            self.add_mixed_dataset_to_model_and_update_view(new_images)

    def add_mixed_dataset_to_model_and_update_view(self, images: ImageStack):
        dataset = MixedDataset([images], images.name)
        self.view._main_window.presenter.model.add_dataset_to_model(dataset)
        self.view._main_window.presenter.create_mixed_dataset_tree_view_items(dataset)
        self.view._main_window.presenter.create_mixed_dataset_stack_windows(dataset)
        self.view._main_window.model_changed.emit()

    def get_num_images(self) -> int:
        return self.images.num_projections

    def find_image_from_angle(self, selected_angle: float) -> int:
        selected_angle = np.deg2rad(selected_angle)
        for index, angle in enumerate(self.images.projection_angles().value):
            if angle >= selected_angle:
                return index
        return len(self.images.projection_angles().value)

    def add_sinograms_to_model_and_update_view(self, new_stack: ImageStack):
        self.view._main_window.presenter.add_sinograms_to_dataset_and_update_view(new_stack, self.images.id)

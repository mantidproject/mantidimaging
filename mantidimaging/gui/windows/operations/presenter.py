# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import traceback
import uuid
from enum import Enum, auto
from functools import partial
from itertools import groupby
from logging import getLogger
from time import sleep
from typing import List, TYPE_CHECKING, Optional, Tuple, Union
from uuid import UUID

import numpy as np
from PyQt5.QtWidgets import QApplication, QLineEdit

from mantidimaging.core.data import ImageStack
from mantidimaging.core.operation_history.const import OPERATION_HISTORY, OPERATION_DISPLAY_NAME
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility import BlockQtSignals
from mantidimaging.gui.utility.common import operation_in_progress
from mantidimaging.gui.windows.stack_choice.presenter import StackChoicePresenter
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

from .model import FiltersWindowModel

APPLY_TO_180_MSG = "Operations applied to the sample are also automatically applied to the " \
      "180 degree projection. Please avoid applying an operation unless you're" \
      " absolutely certain you need to.\nAre you sure you want to apply to 180" \
      " degree projection?"

FLAT_FIELDING = "Flat-fielding"
FLAT_FIELD_REGION = [-0.2, 1.2]

CROP_COORDINATES = "Crop Coordinates"
ROI_NORMALISATION = "ROI Normalisation"

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # pragma: no cover
    from mantidimaging.gui.windows.operations import FiltersWindowView  # pragma: no cover
    from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView

REPEAT_FLAT_FIELDING_MSG = "Do you want to run flat-fielding again? This could cause you to lose data."


class Notification(Enum):
    REGISTER_ACTIVE_FILTER = auto()
    APPLY_FILTER = auto()
    APPLY_FILTER_TO_ALL = auto()
    UPDATE_PREVIEWS = auto()
    SCROLL_PREVIEW_UP = auto()
    SCROLL_PREVIEW_DOWN = auto()


def _find_nan_change(before_image, filtered_image_data):
    """
    Returns a bool array of all the placed where a NaN has been removed.
    :param before_image: The before image.
    :param filtered_image_data: The filter result.
    :return: The indexes of the pixels with removed NaNs.
    """
    before_nan = np.isnan(before_image)
    after_nan = np.isnan(filtered_image_data)
    nan_change = np.logical_and(before_nan, ~after_nan)
    return nan_change


def sub(x: Tuple[int, int]) -> int:
    """
    Subtracts two tuples. Helper method for generating the negative slice list.
    :param x: The int tuple.
    :return: The first value subtracted from the second value.
    """
    return x[1] - x[0]


def _group_consecutive_values(slices: List[int]) -> List[str]:
    """
    Creates a list of slices with negative indices in a readable format.
    :param slices: The list of indices of the slices that contain negative values.
    :return: A list of strings for the index ranges e.g. 1-5, 7-20, etc
    """
    ranges = []
    for k, iterable in groupby(enumerate(slices), sub):
        rng = list(iterable)
        if len(rng) == 1:
            s = str(rng[0][1])
        else:
            s = "{}-{}".format(rng[0][1], rng[-1][1])
        ranges.append(s)

    return ranges


class FiltersWindowPresenter(BasePresenter):
    view: 'FiltersWindowView'
    stack: Optional[ImageStack] = None
    divider = "------------------------------------"

    def __init__(self, view: 'FiltersWindowView', main_window: 'MainWindowView'):
        super().__init__(view)

        self.model = FiltersWindowModel(self)
        self._main_window = main_window

        self.original_images_stack: Union[List[Tuple[ImageStack, UUID]]] = []
        self.applying_to_all = False
        self.filter_is_running = False

        self.prev_apply_single_state = True
        self.prev_apply_all_state = True

    @property
    def main_window(self) -> 'MainWindowView':
        return self._main_window

    def notify(self, signal):
        try:
            if signal == Notification.REGISTER_ACTIVE_FILTER:
                self.do_register_active_filter()
            elif signal == Notification.APPLY_FILTER:
                self.do_apply_filter()
            elif signal == Notification.APPLY_FILTER_TO_ALL:
                self.do_apply_filter_to_all()
            elif signal == Notification.UPDATE_PREVIEWS:
                self.do_update_previews()
            elif signal == Notification.SCROLL_PREVIEW_UP:
                self.do_scroll_preview(1)
            elif signal == Notification.SCROLL_PREVIEW_DOWN:
                self.do_scroll_preview(-1)

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    @property
    def max_preview_image_idx(self):
        if self.stack is None:
            return 0
        if not self.model.selected_filter.operate_on_sinograms:
            return self.stack.num_images - 1
        else:
            return self.stack.num_sinograms - 1

    def set_stack_uuid(self, uuid: Optional[uuid.UUID]):
        if uuid is not None:
            self.set_stack(self.main_window.get_stack(uuid))
        else:
            self.set_stack(None)

    def set_stack(self, stack: Optional[ImageStack]):
        self.stack = stack

        # Update the preview image index
        with BlockQtSignals([self.view]):
            self.set_preview_image_index(0)
            max_slice = self.max_preview_image_idx
            self.view.previewImageIndex.setMaximum(max_slice)
            self.view.previews.z_slider.set_range(0, max_slice)

            for row_id in range(self.view.filterPropertiesLayout.count()):
                widget = self.view.filterPropertiesLayout.itemAt(row_id).widget()
                if isinstance(widget, DatasetSelectorWidgetView):
                    widget._handle_loaded_datasets_changed()

        self.do_update_previews()

    def set_preview_image_index(self, image_idx: int):
        """
        Sets the current preview image index.
        """
        self.model.preview_image_idx = image_idx

        # Set preview index spin box to new index
        preview_idx_spin = self.view.previewImageIndex
        with BlockQtSignals([preview_idx_spin]):
            preview_idx_spin.setValue(self.model.preview_image_idx)

        with BlockQtSignals([self.view.previews.z_slider]):
            self.view.previews.z_slider.set_value(self.model.preview_image_idx)

        # Trigger preview updating
        self.view.auto_update_triggered.emit()

    def do_register_active_filter(self):
        filter_name = self.view.get_selected_filter()

        # Get registration function for new filter
        register_func = self.model.filter_registration_func(filter_name)

        # Register new filter (adding it's property widgets to the properties layout)
        filter_widget_kwargs = register_func(self.view.filterPropertiesLayout, self.view.auto_update_triggered.emit,
                                             self.view)

        if filter_name == CROP_COORDINATES or filter_name == ROI_NORMALISATION:
            self.init_roi_field(filter_widget_kwargs["roi_field"])

        self.model.setup_filter(filter_name, filter_widget_kwargs)
        self.view.clear_notification_dialog()
        self.view.previews.link_before_after_histogram_scales(self.model.link_histograms())

        if self.model.show_negative_overlay():
            self.view.previews.add_negative_overlay()
        else:
            self.view.previews.hide_negative_overlay()

        # Update the preview image index
        with BlockQtSignals([self.view]):
            max_slice = self.max_preview_image_idx
            self.view.previewImageIndex.setMaximum(max_slice)
            self.view.previews.z_slider.set_range(0, max_slice)
            if self.model.preview_image_idx > max_slice:
                self.set_preview_image_index(0)

    def filter_uses_parameter(self, parameter):
        return parameter in self.model.params_needed_from_stack.values() if \
            self.model.params_needed_from_stack is not None else False

    def do_apply_filter(self):
        if self._already_run_flat_fielding():
            if not self.view.ask_confirmation(REPEAT_FLAT_FIELDING_MSG):
                return

        if self.view.safeApply.isChecked():
            with operation_in_progress("Safe Apply: Copying Data", "-------------------------------------", self.view):
                self.original_images_stack = self.stack.copy()

        # if is a 180degree stack and a user says no, cancel apply filter.
        if self.is_a_proj180deg(self.stack) and not self.view.ask_confirmation(APPLY_TO_180_MSG):
            return

        apply_to = [self.stack]

        self._do_apply_filter(apply_to)

    def do_apply_filter_to_all(self):
        confirmed = self.view.ask_confirmation("Are you sure you want to apply this filter to \n\nALL OPEN STACKS?")
        if not confirmed:
            return
        stacks = self.main_window.get_all_stacks()
        if self.view.safeApply.isChecked():
            with operation_in_progress("Safe Apply: Copying Data", "-------------------------------------", self.view):
                self.original_images_stack = []
                for stack in stacks:
                    self.original_images_stack.append((stack.copy(), stack.id))

        if len(stacks) > 0:
            self.applying_to_all = True
        self._do_apply_filter(stacks)

    def _wait_for_stack_choice(self, new_stack: ImageStack, stack_uuid: UUID):
        stack_choice = StackChoicePresenter(self.original_images_stack, new_stack, self, stack_uuid)
        if self.model.show_negative_overlay():
            stack_choice.enable_nonpositive_check()
        stack_choice.show()

        while not stack_choice.done:
            QApplication.processEvents()
            QApplication.sendPostedEvents()
            sleep(0.05)

        return stack_choice.use_new_data

    def is_a_proj180deg(self, stack_to_check: ImageStack):
        return any(stack_to_check is stack for stack in self.main_window.get_all_180_projections())

    def _post_filter(self, updated_stacks: List[ImageStack], task):
        try:
            use_new_data = True
            negative_stacks = []
            for stack in updated_stacks:
                # Ensure there is no error if we are to continue with safe apply and 180 degree.
                if task.error is None:
                    # otherwise check with user which one to keep
                    if self.view.safeApply.isChecked():
                        use_new_data = self._wait_for_stack_choice(stack, stack.id)
                    # if the stack that was kept happened to have a proj180 stack - then apply the filter to that too
                    if stack.has_proj180deg() and use_new_data and not self.applying_to_all:
                        # Apply to proj180 synchronously - this function is already running async
                        # and running another async instance causes a race condition in the parallel module
                        # where the shared data can be removed in the middle of the operation of another operation
                        self._do_apply_filter_sync([stack.proj180deg])
                if np.any(stack.data < 0):
                    negative_stacks.append(stack)

            if self.view.roi_view is not None:
                self.view.roi_view.close()
                self.view.roi_view = None

            self.applying_to_all = False
            self.do_update_previews()

            if task.error is not None:
                # task failed, show why
                self.view.show_error_dialog(f"Operation failed: {task.error}")
            elif use_new_data:
                # Feedback to user
                self.view.clear_notification_dialog()
                self.view.show_operation_completed(self.model.selected_filter.filter_name)

                selected_filter = self.view.get_selected_filter()
                if selected_filter == CROP_COORDINATES:
                    # Reset the ROI field to ensure an appropriate value for the new image size
                    self.init_roi_field(self.model.filter_widget_kwargs["roi_field"])
                elif selected_filter == FLAT_FIELDING and negative_stacks:
                    self._show_negative_values_error(negative_stacks)
            else:
                self.view.clear_notification_dialog()
                self.view.show_operation_cancelled(self.model.selected_filter.filter_name)
        finally:
            self.view.filter_applied.emit()
            self._set_apply_buttons_enabled(self.prev_apply_single_state, self.prev_apply_all_state)
            self.filter_is_running = False

    def _do_apply_filter(self, apply_to: List[ImageStack]):
        self.filter_is_running = True
        # Record the previous button states
        self.prev_apply_single_state = self.view.applyButton.isEnabled()
        self.prev_apply_all_state = self.view.applyToAllButton.isEnabled()
        # Disable the apply buttons
        self._set_apply_buttons_enabled(False, False)
        self.model.do_apply_filter(apply_to, partial(self._post_filter, apply_to))

    def _do_apply_filter_sync(self, apply_to):
        self.model.do_apply_filter_sync(apply_to, partial(self._post_filter, apply_to))

    def do_update_previews(self):
        if self.stack is None:
            self.view.clear_previews()
            return

        is_new_data = self.view.preview_image_before.image_data is None
        is_flat_fielding = self._flat_fielding_is_selected()

        self.view.clear_previews(clear_before=False)

        # Only apply the lock scale after image data has been set for the first time otherwise no region is shown
        lock_scale = self.view.lockScaleCheckBox.isChecked() and not is_new_data
        if lock_scale:
            self.view.previews.record_histogram_regions()
            if is_flat_fielding:
                self.view.previews.after_region = FLAT_FIELD_REGION

        if not self.model.selected_filter.operate_on_sinograms:
            subset: ImageStack = self.stack.slice_as_image_stack(self.model.preview_image_idx)
            squeeze_axis = 0
        else:
            if self.stack.num_projections < 2:
                self.show_error("This filter requires a stack with multiple projections", "")
                self.view.clear_previews()
                return
            subset = self.stack.sino_as_image_stack(self.model.preview_image_idx)
            squeeze_axis = 1

        # Take copies for display to prevent issues when the shared memory is cleaned
        before_image = np.copy(subset.data.squeeze(squeeze_axis))

        try:
            if self.model.filter_widget_kwargs:
                self.model.apply_to_images(subset)
        except Exception as e:
            msg = f"Error applying filter for preview: {e}"
            self.show_error(msg, traceback.format_exc())

            # Can't continue be need the before image drawn
            self._update_preview_image(before_image, self.view.preview_image_before)
            return

        # Update image after first in order to prevent wrong histogram ranges being shared

        filtered_image_data = np.copy(subset.data.squeeze(squeeze_axis))

        if np.any(filtered_image_data < 0):
            self._show_preview_negative_values_error(self.model.preview_image_idx)

        self._update_preview_image(filtered_image_data, self.view.preview_image_after)

        # Update image before
        self._update_preview_image(before_image, self.view.preview_image_before)
        self.view.previews.update_histogram_data()

        if filtered_image_data.shape == before_image.shape:
            diff = np.subtract(filtered_image_data, before_image)
            if self.view.overlayDifference.isChecked():
                nan_change = _find_nan_change(before_image, filtered_image_data)
                self.view.previews.add_difference_overlay(diff, nan_change)
            else:
                self.view.previews.hide_difference_overlay()
            if self.view.invertDifference.isChecked():
                diff = np.negative(diff, out=diff)

            self._update_preview_image(diff, self.view.preview_image_difference)

        # Ensure all of it is visible if the lock zoom isn't checked
        if not self.view.lockZoomCheckBox.isChecked() or is_new_data:
            self.view.previews.auto_range()

        if lock_scale:
            self.view.previews.restore_histogram_regions()
            if is_flat_fielding:
                self.view.preview_image_after.histogram.setHistogramRange(mn=FLAT_FIELD_REGION[0],
                                                                          mx=FLAT_FIELD_REGION[1])
                # We must auto-range the before histogram as when the before and after histograms are linked the
                # change to the after scale is also applied to the before scale
                self.view.preview_image_before.histogram.autoHistogramRange()
        else:
            self.view.previews.autorange_histograms()

        self.view.previews.set_histogram_log_scale()

    @staticmethod
    def _update_preview_image(image_data: Optional[np.ndarray], image: 'MIMiniImageView'):
        image.clear()
        image.setImage(image_data)

    def do_scroll_preview(self, offset):
        idx = self.model.preview_image_idx + offset
        idx = max(min(idx, self.max_preview_image_idx), 0)
        self.set_preview_image_index(idx)

    def get_filter_module_name(self, filter_idx):
        return self.model.get_filter_module_name(filter_idx)

    def set_filter_by_name(self, filter_menu_name: str):
        self.view.filterSelector.setCurrentText(filter_menu_name)

    def _already_run_flat_fielding(self):
        """
        :return: True if this is not the first time flat-fielding is being run, False otherwise.
        """
        if not self._flat_fielding_is_selected():
            return False
        if OPERATION_HISTORY not in self.stack.metadata:
            return False
        return any(operation[OPERATION_DISPLAY_NAME] == FLAT_FIELDING
                   for operation in self.stack.metadata[OPERATION_HISTORY])

    def _set_apply_buttons_enabled(self, apply_single_enabled: bool, apply_all_enabled: bool):
        """
        Changes the state of the apply buttons before/after an operation is run.
        :param apply_single_enabled: The desired state for the apply button.
        :param apply_all_enabled: The desired state for the apply to all button.
        """
        self.view.applyButton.setEnabled(apply_single_enabled)
        self.view.applyToAllButton.setEnabled(apply_all_enabled)

    def init_roi_field(self, roi_field: QLineEdit):
        """
        Sets the initial value of the crop coordinates line edit widget so that it doesn't contain values that are
        larger than the image.
        :param roi_field: The ROI field line edit widget.
        """
        if self.stack is None:
            return

        larger = np.greater(self.stack.data[0].shape, (200, 200))
        if all(larger):
            return
        x = min(self.stack.data[0].shape[0], 200)
        y = min(self.stack.data[0].shape[1], 200)
        crop_string = ", ".join(["0", "0", str(y), str(x)])
        roi_field.setText(crop_string)

    def _show_negative_values_error(self, negative_stacks: List[ImageStack]):
        """
        Shows information on the view and in the log about negative values in the output.
        :param negative_stacks: A list of stacks with negative values in the data.
        """
        operation_name = self.model.selected_filter.filter_name
        gui_error = [f"{operation_name} completed."]

        for stack in negative_stacks:
            negative_slices = []
            for i in range(len(stack.data)):
                if np.any(stack.data[i] < 0):
                    negative_slices.append(i)
            stack_msg = f'Slices containing negative values in {stack.name}: '
            if len(negative_slices) == len(stack.data):
                slices_msg = stack_msg + "all slices."
                gui_error.append(slices_msg)
            else:
                ranges = _group_consecutive_values(negative_slices)
                slices_msg = stack_msg + f'{", ".join(ranges)}.'
                if len(negative_slices) <= 12:
                    gui_error.append(slices_msg)
                else:
                    gui_error.append(f'{stack_msg}{", ".join(ranges[:10])} ... {ranges[-1]}.')
            getLogger(__name__).error(slices_msg)
        self.view.show_error_dialog(" ".join(gui_error))

    def _show_preview_negative_values_error(self, slice_idx: int):
        """
        Shows a message that the operation preview contains negative values.
        :param slice_idx: The index of the preview slice.
        """
        self.view.show_error_dialog(f"Negative values found in result preview for slice {slice_idx}.")

    def _flat_fielding_is_selected(self):
        return self.view.get_selected_filter() == FLAT_FIELDING

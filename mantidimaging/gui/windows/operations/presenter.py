# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import traceback
from enum import Enum, auto
from functools import partial
from logging import getLogger
from time import sleep
from typing import List, TYPE_CHECKING, Optional, Tuple, Union
from uuid import UUID

import numpy as np
from PyQt5.QtWidgets import QApplication
from pyqtgraph import ImageItem

from mantidimaging.core.data import Images
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility import BlockQtSignals
from mantidimaging.gui.utility.common import operation_in_progress
from mantidimaging.gui.windows.stack_choice.presenter import StackChoicePresenter
from mantidimaging.gui.windows.stack_visualiser.view import StackVisualiserView

from .model import FiltersWindowModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # pragma: no cover
    from mantidimaging.gui.windows.operations import FiltersWindowView  # pragma: no cover


REPEAT_FLAT_FIELDING_MSG = "Do you want to run flat-fielding again? This could cause you to lose data."


class Notification(Enum):
    REGISTER_ACTIVE_FILTER = auto()
    APPLY_FILTER = auto()
    APPLY_FILTER_TO_ALL = auto()
    UPDATE_PREVIEWS = auto()
    SCROLL_PREVIEW_UP = auto()
    SCROLL_PREVIEW_DOWN = auto()


class FiltersWindowPresenter(BasePresenter):
    view: 'FiltersWindowView'
    stack: Optional[StackVisualiserView] = None
    divider = "------------------------------------"

    def __init__(self, view: 'FiltersWindowView', main_window: 'MainWindowView'):
        super(FiltersWindowPresenter, self).__init__(view)

        self.model = FiltersWindowModel(self)
        self._main_window = main_window

        self.original_images_stack: Union[List[Tuple[Images, UUID]]] = []
        self.applying_to_all = False

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
        num_images = self.stack.presenter.images.num_images if self.stack is not None else 0
        return max(num_images - 1, 0)

    def set_stack_uuid(self, uuid):
        self.set_stack(self.main_window.get_stack_visualiser(uuid) if uuid is not None else None)

    def set_stack(self, stack):
        self.stack = stack

        # Update the preview image index
        with BlockQtSignals([self.view]):
            self.set_preview_image_index(0)
            self.view.previewImageIndex.setMaximum(self.max_preview_image_idx)

        self.do_update_previews()

    def set_preview_image_index(self, image_idx):
        """
        Sets the current preview image index.
        """
        self.model.preview_image_idx = image_idx

        # Set preview index spin box to new index
        preview_idx_spin = self.view.previewImageIndex
        with BlockQtSignals([preview_idx_spin]):
            preview_idx_spin.setValue(self.model.preview_image_idx)

        # Trigger preview updating
        self.view.auto_update_triggered.emit()

    def do_register_active_filter(self):
        filter_name = self.view.filterSelector.currentText()

        # Get registration function for new filter
        register_func = self.model.filter_registration_func(filter_name)

        # Register new filter (adding it's property widgets to the properties layout)
        filter_widget_kwargs = register_func(self.view.filterPropertiesLayout, self.view.auto_update_triggered.emit,
                                             self.view)
        self.model.setup_filter(filter_name, filter_widget_kwargs)
        self.view.clear_notification_dialog()

    def filter_uses_parameter(self, parameter):
        return parameter in self.model.params_needed_from_stack.values() if \
            self.model.params_needed_from_stack is not None else False

    def do_apply_filter(self):

        if self._already_run_flat_fielding():
            if not self.view.ask_confirmation(REPEAT_FLAT_FIELDING_MSG)
                return

        if self.view.safeApply.isChecked():
            with operation_in_progress("Safe Apply: Copying Data", "-------------------------------------", self.view):
                self.original_images_stack = self.stack.presenter.images.copy()

        # if is a 180degree stack and a user says no, cancel apply filter.
        if self.is_a_proj180deg(self.stack) \
            and not self.view.ask_confirmation("Operations applied to the sample are also automatically applied to the "
                                               "180 degree projection. Please avoid applying an operation unless you're"
                                               " absolutely certain you need to.\nAre you sure you want to apply to 180"
                                               " degree projection?"):
            return

        apply_to = [self.stack]

        self._do_apply_filter(apply_to)

    def do_apply_filter_to_all(self):
        confirmed = self.view.ask_confirmation(REPEAT_FLAT_FIELDING_MSG)
        if not confirmed:
            return
        if self._already_run_flat_fielding():
            if not self.view.ask_confirmation("Do you want to run flat-fielding again? This could cause you to lose data.")
                return
        stacks = self.main_window.get_all_stack_visualisers()
        if self.view.safeApply.isChecked():
            with operation_in_progress("Safe Apply: Copying Data", "-------------------------------------", self.view):
                self.original_images_stack = []
                for stack in stacks:
                    self.original_images_stack.append((stack.presenter.images.copy(), stack.uuid))

        if len(stacks) > 0:
            self.applying_to_all = True
        self._do_apply_filter(stacks)

    def _wait_for_stack_choice(self, new_stack: Images, stack_uuid: UUID):
        stack_choice = StackChoicePresenter(self.original_images_stack, new_stack, self, stack_uuid)
        stack_choice.show()

        while not stack_choice.done:
            QApplication.processEvents()
            QApplication.sendPostedEvents()
            sleep(0.05)

        return stack_choice.use_new_data

    def is_a_proj180deg(self, stack_to_check: StackVisualiserView):
        if stack_to_check.presenter.images.has_proj180deg():
            return False
        stacks = self.main_window.get_all_stack_visualisers()
        for stack in stacks:
            if stack.presenter.images.proj180deg == stack_to_check.presenter.images:
                return True
        return False

    def _post_filter(self, updated_stacks: List[StackVisualiserView], task):
        do_180deg = True
        attempt_repair = task.error is not None
        for stack in updated_stacks:
            # If the operation encountered an error during processing,
            # try to restore the original data else continue processing as usual
            if attempt_repair:
                self.main_window.presenter.model.set_images_in_stack(stack.uuid, stack.presenter.images)
            # Ensure there is no error if we are to continue with safe apply and 180 degree.
            elif task.error is None:
                # otherwise check with user which one to keep
                if self.view.safeApply.isChecked():
                    do_180deg = self._wait_for_stack_choice(stack.presenter.images, stack.uuid)
                # if the stack that was kept happened to have a proj180 stack - then apply the filter to that too
                if stack.presenter.images.has_proj180deg() and do_180deg and not self.applying_to_all:
                    self.view.clear_previews()
                    # Apply to proj180 synchronously - this function is already running async
                    # and running another async instance causes a race condition in the parallel module
                    # where the shared data can be removed in the middle of the operation of another operation
                    self._do_apply_filter_sync(
                        [self.view.main_window.get_stack_with_images(stack.presenter.images.proj180deg)])
                    self.view.main_window.update_stack_with_images(stack.presenter.images.proj180deg)
                self.view.main_window.update_stack_with_images(stack.presenter.images)

        if self.view.roi_view is not None:
            self.view.roi_view.close()
            self.view.roi_view = None

        self.applying_to_all = False
        self.do_update_previews()

        if task.error is not None:
            # task failed, show why
            self.view.show_error_dialog(f"Operation failed: {task.error}")
        else:
            # Feedback to user
            self.view.clear_notification_dialog()
            self.view.show_operation_completed(self.model.selected_filter.filter_name)

    def _do_apply_filter(self, apply_to):
        self.model.do_apply_filter(apply_to, partial(self._post_filter, apply_to))

    def _do_apply_filter_sync(self, apply_to):
        self.model.do_apply_filter_sync(apply_to, partial(self._post_filter, apply_to))

    def do_update_previews(self):
        self.view.clear_previews()
        if self.stack is not None:
            stack_presenter = self.stack.presenter
            subset: Images = stack_presenter.get_image(self.model.preview_image_idx)
            before_image = np.copy(subset.data[0])
            # Update image before
            self._update_preview_image(before_image, self.view.preview_image_before)

            try:
                self.model.apply_to_images(subset)
            except Exception as e:
                msg = f"Error applying filter for preview: {e}"
                self.show_error(msg, traceback.format_exc())
                return

            filtered_image_data = subset.data[0]

            self._update_preview_image(filtered_image_data, self.view.preview_image_after)

            self.view.previews.update_histogram_data()

            if filtered_image_data.shape == before_image.shape:
                diff = np.subtract(filtered_image_data, before_image)
                if self.view.overlayDifference.isChecked():
                    self.view.previews.add_difference_overlay(diff)
                else:
                    self.view.previews.hide_difference_overlay()
                if self.view.invertDifference.isChecked():
                    diff = np.negative(diff, out=diff)
                self._update_preview_image(diff, self.view.preview_image_difference)

            # Ensure all of it is visible
            self.view.previews.auto_range()

    @staticmethod
    def _update_preview_image(image_data: Optional[np.ndarray], image: ImageItem):
        image.clear()
        image.setImage(image_data)

    def do_scroll_preview(self, offset):
        idx = self.model.preview_image_idx + offset
        idx = max(min(idx, self.max_preview_image_idx), 0)
        self.set_preview_image_index(idx)

    def get_filter_module_name(self, filter_idx):
        return self.model.get_filter_module_name(filter_idx)

    def _already_run_flat_fielding(self):
        if self.view.filterSelector.currentText() is not "Flat-fielding":
            return False

        # return flat-fielding in operation history

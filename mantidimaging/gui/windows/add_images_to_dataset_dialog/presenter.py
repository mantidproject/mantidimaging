# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import traceback
from enum import Enum, auto
from typing import TYPE_CHECKING

from mantidimaging.gui.dialogs.async_task import start_async_task_view, TaskWorkerThread
from mantidimaging.gui.mvp_base import BasePresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.add_images_to_dataset_dialog.view import AddImagesToDatasetDialog


class Notification(Enum):
    IMAGE_FILE_SELECTED = auto()


class AddImagesToDatasetPresenter(BasePresenter):
    view: AddImagesToDatasetDialog

    def __init__(self, view: AddImagesToDatasetDialog):
        super().__init__(view)
        self._images = None

    def notify(self, n: Notification) -> None:
        try:
            if n == Notification.IMAGE_FILE_SELECTED:
                self.load_images()
        except RuntimeError as err:
            self.view.show_exception(str(err), traceback.format_exc())

    def load_images(self) -> None:
        """
        Loads the images from the file path provided by the user.
        """
        start_async_task_view(self.view, self.view.parent_view.presenter.model.load_image_stack,
                              self._on_images_load_done, {'file_path': self.view.path})

    def _on_images_load_done(self, task: TaskWorkerThread) -> None:
        """
        Checks if loading images was successful and then triggers the necessary updates.
        :param task: The file loading task.
        """
        if task.was_successful():
            self._images = task.result
            self.view.parent_view.execute_add_to_dataset()
        else:
            self.show_error(task.error, traceback.format_exc())

    @property
    def images(self):
        return self._images

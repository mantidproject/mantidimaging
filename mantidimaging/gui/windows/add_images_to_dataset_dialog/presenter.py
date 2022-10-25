# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os.path
import traceback
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantidimaging.gui.windows.add_images_to_dataset_dialog.view import AddImagesToDatasetDialog


class Notification(Enum):
    IMAGE_FILE_SELECTED = auto()


class AddImagesToDatasetPresenter:
    view: 'AddImagesToDatasetDialog'

    def __init__(self, view: 'AddImagesToDatasetDialog'):
        self.view = view

    def notify(self, n: Notification):
        try:
            if n == Notification.IMAGE_FILE_SELECTED:
                self.find_images()
        except RuntimeError as err:
            self.view.show_exception(str(err), traceback.format_exc())

    def find_images(self):
        image_path = self.view.path
        directory = os.path.dirname(image_path)
        print(image_path)
        print(directory)

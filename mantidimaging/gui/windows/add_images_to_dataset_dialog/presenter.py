# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from enum import Enum, auto
from typing import TYPE_CHECKING

from mantidimaging.core.io.loader import load_stack

if TYPE_CHECKING:
    from mantidimaging.gui.windows.add_images_to_dataset_dialog.view import AddImagesToDatasetDialog


class Notification(Enum):
    IMAGE_FILE_SELECTED = auto()


class AddImagesToDatasetPresenter:
    view: 'AddImagesToDatasetDialog'

    def __init__(self, view: 'AddImagesToDatasetDialog'):
        self.view = view

    def load_images(self):
        image_path = self.view.path
        return load_stack(image_path)

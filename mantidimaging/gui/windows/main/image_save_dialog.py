# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from mantidimaging.core.io.loader import supported_formats
from mantidimaging.core.io.utility import DEFAULT_IO_FILE_FORMAT
from mantidimaging.gui.utility import (compile_ui, select_directory)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main.presenter import StackId


def sort_by_tomo_and_recon(stack_id: "StackId"):
    if "Recon" in stack_id.name:
        return 1
    elif "Tomo" in stack_id.name:
        return 2
    else:
        return 3


class ImageSaveDialog(QDialog):
    selected_stack = Optional[uuid.UUID]

    def __init__(self, parent, stack_list):
        super().__init__(parent)
        compile_ui('gui/ui/image_save_dialog.ui', self)

        self.browseButton.clicked.connect(lambda: select_directory(self.savePath, "Browse"))

        self.buttonBox.button(QDialogButtonBox.StandardButton.SaveAll).clicked.connect(self.save_all)

        # dynamically add all the supported formats
        formats = supported_formats()
        self.formats.addItems(formats)

        # set the default to tiff
        self.formats.setCurrentIndex(formats.index(DEFAULT_IO_FILE_FORMAT))

        if stack_list:  # we will just show an empty drop down if no stacks
            # Sort stacknames using Recon and Tomo as preference
            user_friendly_stack_list = sorted(stack_list, key=sort_by_tomo_and_recon)
            # the stacklist is created in the main windows presenter and has
            # format [(uuid, title)...], doing zip(*stack_list) unzips the
            # tuples into separate lists
            self.stack_uuids, user_friendly_names = zip(*user_friendly_stack_list)

            self.stackNames.addItems(user_friendly_names)

        self.selected_stack = None

    def save_all(self):
        self.selected_stack = self.stack_uuids[self.stackNames.currentIndex()]
        self.parent().execute_save()

    def save_path(self) -> str:
        """
            :return: The directory of the path as a Python string
        """
        return str(self.savePath.text())

    def name_prefix(self) -> str:
        """
            :return: The directory of the path as a Python string
        """
        return str(self.namePrefix.text())

    def overwrite(self) -> bool:
        return self.overwriteAll.isChecked()

    def image_format(self) -> str:
        return str(self.formats.currentText())

    def pixel_depth(self) -> str:
        return str(self.pixelDepth.currentText())

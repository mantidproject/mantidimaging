# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import inspect
import os
from tempfile import mkdtemp
from uuid import uuid4

from PyQt5.QtWidgets import QWidget, QApplication
from applitools.common import BatchInfo, MatchLevel
from applitools.images import Eyes

from mantidimaging.gui.windows.main import MainWindowView


class EyesManager:
    def __init__(self, application_name="Mantid Imaging", test_name=None):
        self.application_name = application_name
        self.eyes = Eyes()
        self.eyes.match_level = MatchLevel.LAYOUT
        self.image_directory = None
        self.imaging = None
        if test_name is None:
            test_name = self.application_name + " Tests"
        self.test_name = test_name

    def set_match_level(self, level: MatchLevel):
        self.eyes.match_level = level

    def set_batch(self, batch_id):
        batch_info = BatchInfo()
        batch_info.name = self.test_name
        batch_info.id = batch_id
        self.eyes.batch = batch_info

    def abort(self):
        self.eyes.abort_if_not_closed()

    def check_target(self, widget: QWidget = None):
        test_file_name = os.path.basename(inspect.stack()[2][1])
        test_method_name = inspect.stack()[2][3]
        test_image_name = test_file_name.rpartition(".")[0] + "_" + test_method_name

        image = self._take_screenshot(widget=widget, image_name=test_image_name)

        if self.eyes.api_key == "local":
            return

        if not self.eyes.is_open:
            self.eyes.open(self.application_name, test_file_name)
        self.eyes.check_image(image, test_method_name)

    def close_imaging(self):
        self.imaging.close()

    def start_imaging(self):
        self.imaging = MainWindowView(open_dialogs=False)
        self.imaging.show()
        QApplication.processEvents()

    def _take_screenshot(self, widget: QWidget = None, image_name=None):
        """
        :param widget: Widget to take screen shot of or main window if None.
        :param image_name: File name for screenshot
        :return: Will return the path to the saved image, or None if failed.
        """
        if self.image_directory is None:
            directory = mkdtemp()
        else:
            directory = self.image_directory

        if widget is None and self.imaging is not None:
            widget = self.imaging

        if isinstance(widget, QWidget):
            QApplication.processEvents()
            image = widget.grab()
        else:
            image = None

        if image_name is None:
            image_name = str(uuid4())

        file_path = os.path.join(directory, image_name) + ".png"

        if image.save(file_path, "PNG"):
            return file_path
        else:
            raise IOError("Failed to save", file_path)

    def close_eyes(self):
        if self.eyes.is_open:
            self.eyes.close()

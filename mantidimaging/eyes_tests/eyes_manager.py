# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
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
    def __init__(self, application_name="Mantid Imaging"):
        self.application_name = application_name
        self.eyes = Eyes()
        self.eyes.match_level = MatchLevel.LAYOUT
        self.image_directory = None
        self.imaging = None

    def set_batch(self, batch_id):
        batch_info = BatchInfo()
        batch_info.name = self.application_name + " Tests"
        batch_info.id = batch_id
        self.eyes.batch = batch_info

    def abort(self):
        self.eyes.abort_if_not_closed()

    def check_target(self, image=None, widget: QWidget = None):
        if image is None:
            image = self._take_screenshot(widget=widget)
        test_method_name = inspect.stack()[2][3]
        if not self.eyes.is_open:
            test_file_name = os.path.basename(inspect.stack()[2][1])
            self.eyes.open(self.application_name, test_file_name)
        self.eyes.check_image(image, test_method_name)

    def close_imaging(self):
        self.imaging.close()

    def start_imaging(self):
        self.imaging = MainWindowView(open_dialogs=False)
        self.imaging.show()
        QApplication.processEvents()

    def _take_screenshot(self, widget: QWidget = None, directory=None):
        """
        :param directory: The directory to save the screenshot to, should be a temporary directory. If None is given it
        will generate a temporary directory.

        :return: Will return the path to the saved image, or None if failed.
        """
        if directory is None and self.image_directory is None:
            directory = mkdtemp()
        elif directory is None:
            directory = self.image_directory

        if widget is None and self.imaging is not None:
            widget = self.imaging

        image = widget.grab()

        file_path = os.path.join(directory, str(uuid4()))
        if image.save(file_path, "PNG"):
            return file_path

    def close_eyes(self):
        if self.eyes.is_open:
            self.eyes.close()

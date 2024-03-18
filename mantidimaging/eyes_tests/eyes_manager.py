# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import inspect
import os
import sys
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any
from unittest import mock
from uuid import uuid4

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtTest import QTest

from mantidimaging.gui.windows.main import MainWindowView

# COMPAT: applitools has some bad signatures, so avoid importing it when type checking
# See https://github.com/mantidproject/mantidimaging/issues/2008
if not TYPE_CHECKING:
    from applitools.common import BatchInfo, MatchLevel
    from applitools.images import Eyes
else:
    MatchLevel = Any

# Used to disabiguate tests on the Applitools platform. set explicitly to avoid depending on the window size
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080


class EyesManager:

    def __init__(self, application_name="Mantid Imaging", test_name=None):
        self.application_name = application_name
        self.eyes = Eyes()
        self.eyes.match_level = MatchLevel.IGNORE_COLORS
        self.eyes.configure.host_os = sys.platform
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
            self.eyes.open(self.application_name,
                           test_file_name,
                           dimension={
                               'width': VIEWPORT_WIDTH,
                               'height': VIEWPORT_HEIGHT
                           })
        self.eyes.check_image(image, test_method_name)

    def close_imaging(self):
        self.imaging.close()

    def start_imaging(self):
        self.imaging = MainWindowView(open_dialogs=False)
        self.imaging.ask_to_use_closest_to_180 = mock.Mock(return_value=False)
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

        if not isinstance(widget, QWidget):
            raise ValueError("widget is not a QWidget")

        QTest.qWaitForWindowExposed(widget)
        QApplication.sendPostedEvents()
        QApplication.processEvents()
        window_image = widget.grab()

        if image_name is None:
            image_name = str(uuid4())

        file_path = os.path.join(directory, image_name) + ".png"

        if window_image.save(file_path, "PNG"):
            return file_path
        else:
            raise OSError("Failed to save", file_path)

    def close_eyes(self):
        if self.eyes.is_open:
            self.eyes.close()

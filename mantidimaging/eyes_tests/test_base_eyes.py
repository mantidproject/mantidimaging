import inspect
import os
import unittest
from tempfile import mkdtemp
from uuid import uuid4

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget
from applitools.images import Eyes
from applitools.common import logger, StdoutLogger, MatchLevel
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.test_helpers.start_qapplication import start_qapplication


logger.set_logger(StdoutLogger())


@start_qapplication
class BaseEyesTest(unittest.TestCase):
    def setUp(self):
        self.eyes = None
        self.imaging = None
        self.image_directory = mkdtemp()

        # Do setup
        self.start_imaging()

    def tearDown(self):
        if self.imaging is not None:
            self.close_imaging()

    def check_target(self, image=None):
        self.eyes = Eyes()
        viewport_size = {'width': 1920, 'height': 1080}
        self.eyes.open("Mantid Imaging", str(self.__class__.__name__), viewport_size)
        if image is None:
            image = self._take_screenshot()
        try:
            self.eyes.check_image(image, str(inspect.stack()[1][3]))
            throwTestCompleteException = False
            return self.eyes.close(throwTestCompleteException)
        finally:
            self.eyes.abort_if_not_closed()

    def start_imaging(self):
        self.imaging = MainWindowView(open_dialogs=False)
        self.imaging.show()
        QApplication.processEvents()

    def close_imaging(self):
        self.imaging.close()

    def _take_screenshot(self, widget: QWidget=None, directory=None):
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

import unittest
from tempfile import mkdtemp
from uuid import uuid4

from PyQt5.QtWidgets import QMainWindow, QMenu, QWidget

from eyes_tests.eyes_manager import EyesManager
from mantidimaging.test_helpers.start_qapplication import start_qapplication


RUN_UUID = uuid4()


@start_qapplication
class BaseEyesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.eyes_manager = EyesManager("Mantid Imaging")
        cls.eyes_manager.set_batch(RUN_UUID)

    def setUp(self):
        self.imaging = None
        self.eyes_manager.image_directory = mkdtemp()

        # Do setup
        self.eyes_manager.start_imaging()

    def tearDown(self):
        if self.imaging is not None:
            self.eyes_manager.close_imaging()
        self.eyes_manager.abort()

    @property
    def imaging(self):
        return self.eyes_manager.imaging

    @imaging.setter
    def imaging(self, imaging):
        self.eyes_manager.imaging = imaging

    def check_target(self, image=None, widget: QWidget = None):
        self.eyes_manager.check_target(image, widget)

    @staticmethod
    def show_menu(widget: QMainWindow, menu: QMenu):
        menu_location = widget.menuBar().rect().bottomLeft()
        menu.popup(widget.mapFromGlobal(menu_location))

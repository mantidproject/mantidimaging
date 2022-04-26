# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
import unittest
import getpass
from pathlib import Path
from tempfile import mkdtemp
from uuid import uuid4

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QMenu, QWidget, QApplication
from applitools.common import MatchLevel

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.core.io.loader import loader
from mantidimaging.eyes_tests.eyes_manager import EyesManager
from mantidimaging.test_helpers.start_qapplication import start_qapplication
import mantidimaging.core.parallel.utility as pu

# APPLITOOLS_BATCH_ID will be set by Github actions to the commit SHA, or a random UUID for individual developer
# execution

APPLITOOLS_BATCH_ID = os.getenv("APPLITOOLS_BATCH_ID")
if APPLITOOLS_BATCH_ID is None:
    APPLITOOLS_BATCH_ID = str(uuid4())

API_KEY_PRESENT = os.getenv("APPLITOOLS_API_KEY")

TEST_NAME = os.getenv("GITHUB_BRANCH_NAME")
if TEST_NAME is None:
    TEST_NAME = f"{getpass.getuser()}'s Local Test"

LOAD_SAMPLE = str(Path.home()) + "/mantidimaging-data/ISIS/IMAT/IMAT00010675/Tomo/IMAT_Flower_Tomo_000000.tif"
LOAD_SAMPLE_MISSING_MESSAGE = """Data not present, please clone to your home directory e.g.
git clone https://github.com/mantidproject/mantidimaging-data.git"""

NEXUS_SAMPLE = str(
    Path.home()) + "/mantidimaging-data/Diamond/i13/AKingUVA_7050wSSwire_InSitu_95RH_2MMgCl2_p4ul_p4h/24737.nxs"

APPLITOOLS_IMAGE_DIR = os.getenv("APPLITOOLS_IMAGE_DIR")
if APPLITOOLS_IMAGE_DIR is None:
    APPLITOOLS_IMAGE_DIR = mkdtemp(prefix="mantid_image_eyes_")
else:
    if not os.path.isdir(APPLITOOLS_IMAGE_DIR):
        raise ValueError(f"Directory does not exist: APPLITOOLS_IMAGE_DIR = {APPLITOOLS_IMAGE_DIR}")

QApplication.setFont(QFont("Sans Serif", 10))


@unittest.skipIf(API_KEY_PRESENT is None, "API Key is not defined in the environment, so Eyes tests are skipped.")
@unittest.skipUnless(os.path.exists(LOAD_SAMPLE), LOAD_SAMPLE_MISSING_MESSAGE)
@start_qapplication
class BaseEyesTest(unittest.TestCase):
    eyes_manager: EyesManager

    @classmethod
    def setUpClass(cls) -> None:
        cls.eyes_manager = EyesManager("Mantid Imaging", test_name=TEST_NAME)
        cls.eyes_manager.set_batch(APPLITOOLS_BATCH_ID)

    def setUp(self):
        self.eyes_manager.set_match_level(MatchLevel.CONTENT)

        self.imaging = None
        self.eyes_manager.image_directory = APPLITOOLS_IMAGE_DIR

        self.stacks = []

        # Do setup
        self.eyes_manager.start_imaging()

    def tearDown(self):
        if self.imaging is not None:
            self.eyes_manager.close_imaging()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.eyes_manager.close_eyes()

    @property
    def imaging(self):
        return self.eyes_manager.imaging

    @imaging.setter
    def imaging(self, imaging):
        self.eyes_manager.imaging = imaging

    def check_target(self, widget: QWidget = None):
        self.eyes_manager.check_target(widget)

    @staticmethod
    def show_menu(widget: QMainWindow, menu: QMenu):
        menu_location = widget.menuBar().rect().bottomLeft()
        menu.popup(widget.mapFromGlobal(menu_location))

    def _load_data_set(self, set_180: bool = False):
        image_stack = loader.load(file_names=[LOAD_SAMPLE])
        dataset = StrictDataset(image_stack)
        image_stack.name = "Stack 1"
        vis = self.imaging.presenter.create_strict_dataset_stack_windows(dataset)
        self.imaging.presenter.create_strict_dataset_tree_view_items(dataset)

        if set_180:
            _180_array = image_stack.data[0:1]
            shared_180 = pu.create_array(_180_array.shape, _180_array.dtype)
            shared_180.array[:] = _180_array[:]
            image_stack.proj180deg = ImageStack(shared_180)
            self.imaging.presenter.create_single_tabbed_images_stack(image_stack.proj180deg)

        self.imaging.presenter.model.add_dataset_to_model(dataset)

        QApplication.sendPostedEvents()

        return vis

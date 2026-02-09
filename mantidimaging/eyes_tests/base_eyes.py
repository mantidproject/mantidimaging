# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import unittest
import getpass
from pathlib import Path
from tempfile import mkdtemp
import logging
from uuid import uuid4

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QMenu, QWidget, QApplication

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.eyes_tests.eyes_manager import EyesManager
from mantidimaging.test_helpers.start_qapplication import start_qapplication
from mantidimaging.test_helpers.unit_test_helper import generate_images

import matplotlib.pyplot  # noqa: F401 - need to import before FakeFileSystem, see Issue #2480

# APPLITOOLS_BATCH_ID will be set by Github actions to the commit SHA, or a random UUID for individual developer
# execution
logger = logging.getLogger(__name__)


def get_env_var(name: str, default: str | None = None, required: bool = False) -> str:
    """
    Retrieve an environment variable value with optional default, logging, and required flag.

    :param name: Name of the environment variable
    :param default: Default value if the variable is not set
    :param required: If True, raises RuntimeError if variable is unset
    :return: The value of the environment variable or default
    """
    value = os.getenv(name, default)

    if value is not None:
        logger.debug(f"Environment variable '{name}' found with value: {value}")
        return value
    else:
        if required:
            logger.error(f"Required environment variable '{name}' is not set.")
            raise RuntimeError(f"Required environment variable '{name}' is not set.")
        logger.info(f"Environment variable '{name}' not set; using default: {default}")
        return default if default is not None else ""


API_KEY_PRESENT = get_env_var("APPLITOOLS_API_KEY")
TEST_NAME = get_env_var("GITHUB_BRANCH_NAME", default=f"{getpass.getuser()}'s Local Test")
APPLITOOLS_BATCH_ID = get_env_var("APPLITOOLS_BATCH_ID", default=str(uuid4()))
env_data_path = get_env_var("MANTIDIMAGING_DATA_DIR")

POTENTIAL_DATA_DIRS = []
if env_data_path:
    POTENTIAL_DATA_DIRS.append(Path(env_data_path))
POTENTIAL_DATA_DIRS.extend(
    [Path(__file__).resolve().parent.parent / "mantidimaging-data",
     Path.home() / "mantidimaging-data"])

POTENTIAL_DATA_DIRS = [p for p in POTENTIAL_DATA_DIRS if p is not None]
DATA_ROOT = next((candidate for candidate in POTENTIAL_DATA_DIRS if candidate.is_dir()), None)

if DATA_ROOT is None:
    raise RuntimeError("mantidimaging-data repository not found in any known location.\n"
                       "Please clone it beside mantidimaging-dev, "
                       "in your home directory, or set MANTIDIMAGING_DATA_DIR.")

LOAD_SAMPLE = DATA_ROOT / "ISIS/IMAT/IMAT00010675/Tomo/IMAT_Flower_Tomo_000000.tif"
LOAD_SAMPLE_MISSING_MESSAGE = ("Data not present, please clone e.g.:\n"
                               "git clone https://github.com/mantidproject/mantidimaging-data.git\n")
NEXUS_SAMPLE = DATA_ROOT / "Diamond/i13/AKingUVA_7050wSSwire_InSitu_95RH_2MMgCl2_p4ul_p4h/24737.nxs"
applitools_image_dir_str = get_env_var("APPLITOOLS_IMAGE_DIR", default=mkdtemp(prefix="mantid_image_eyes_"))
APPLITOOLS_IMAGE_DIR = Path(applitools_image_dir_str)

if not APPLITOOLS_IMAGE_DIR.is_dir():
    raise ValueError(f"Directory does not exist: APPLITOOLS_IMAGE_DIR = {APPLITOOLS_IMAGE_DIR}")

QApplication.setFont(QFont("Sans Serif", 10))


@unittest.skipIf(API_KEY_PRESENT is None, "API Key is not defined in the environment, so Eyes tests are skipped.")
@unittest.skipUnless(LOAD_SAMPLE.exists(), LOAD_SAMPLE_MISSING_MESSAGE)
@start_qapplication
class BaseEyesTest(unittest.TestCase):
    eyes_manager: EyesManager
    app: QApplication

    @classmethod
    def setUpClass(cls) -> None:
        cls.eyes_manager = EyesManager("Mantid Imaging", test_name=TEST_NAME)
        cls.eyes_manager.set_batch(APPLITOOLS_BATCH_ID)

    def setUp(self):
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

    def _create_new_dataset(self) -> Dataset:
        new_dataset = Dataset(sample=generate_images(), name="new")
        self.imaging.presenter.create_dataset_stack_visualisers(new_dataset)
        self.imaging.presenter.model.add_dataset_to_model(new_dataset)
        self.imaging.presenter.update_dataset_tree()

        QApplication.sendPostedEvents()

        return new_dataset

    def _get_top_level_widget(self, widget_type):
        for widget in self.app.topLevelWidgets():
            if isinstance(widget, widget_type):
                return widget
        raise ValueError(f"Could not find top level widget of type {widget_type.__name__}")

# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from unittest import mock

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class MainWindowTest(BaseEyesTest):
    def setUp(self):
        super().setUp()

    def test_main_window_opens(self):
        self.check_target()

    def test_main_window_opens_image_loaded(self):
        self.imaging.presenter = mock.MagicMock()
        self.imaging.presenter.stack_names = [""]
        self.imaging.update_shortcuts()

        self.check_target()

    def test_main_window_file_menu(self):
        self.show_menu(self.imaging, self.imaging.menuFile)
        self.check_target(widget=self.imaging.menuFile)

    def test_main_window_file_menu_image_loaded(self):
        self.imaging.presenter = mock.MagicMock()
        self.imaging.presenter.stacks = {"": ""}
        self.imaging.update_shortcuts()

        self.show_menu(self.imaging, self.imaging.menuFile)
        self.check_target(widget=self.imaging.menuFile)

    def test_main_window_help_menu(self):
        self.show_menu(self.imaging, self.imaging.menuHelp)
        self.check_target(widget=self.imaging.menuHelp)

    def test_main_window_workflow_menu(self):
        self.show_menu(self.imaging, self.imaging.menuWorkflow)
        self.check_target(widget=self.imaging.menuWorkflow)

    def test_main_window_workflow_menu_image_loaded(self):
        self.imaging.presenter = mock.MagicMock()
        self.imaging.presenter.stack_names = [""]
        self.imaging.update_shortcuts()

        self.show_menu(self.imaging, self.imaging.menuWorkflow)
        self.check_target(widget=self.imaging.menuWorkflow)

    def test_main_window_image_menu(self):
        self._load_data_set()
        self.show_menu(self.imaging, self.imaging.menuImage)

        self.check_target(widget=self.imaging.menuImage)

    def test_main_window_loaded_data(self):
        self._load_data_set()

        self.check_target()

    def test_main_window_loaded_2_sets_of_data(self):
        self._load_data_set()
        self._load_data_set()

        self.check_target()

    def test_single_click_changes_tab(self):
        self._load_data_set()
        self._load_data_set()

        second_stack_item = self.imaging.dataset_tree_widget.topLevelItem(1).child(0)
        second_stack_rect = self.imaging.dataset_tree_widget.visualItemRect(second_stack_item)
        QTest.mouseClick(self.imaging.dataset_tree_widget.viewport(), Qt.LeftButton, Qt.NoModifier,
                         second_stack_rect.center())

        self.check_target()

    def test_dataset_tree_view_menu(self):
        self._load_data_set()

        dataset_tree_view_item = self.imaging.dataset_tree_widget.topLevelItem(0).child(0)
        dataset_tree_item_rect = self.imaging.dataset_tree_widget.visualItemRect(dataset_tree_view_item)
        QTest.mouseClick(self.imaging.dataset_tree_widget.viewport(), Qt.RightButton, Qt.NoModifier,
                         dataset_tree_item_rect.center())

        self.check_target()

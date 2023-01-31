# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

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
        self._load_strict_data_set()
        self.show_menu(self.imaging, self.imaging.menuImage)

        self.check_target(widget=self.imaging.menuImage)

    def test_main_window_loaded_data(self):
        self._load_strict_data_set()

        self.check_target()

    def test_main_window_loaded_2_sets_of_data(self):
        self._load_strict_data_set()
        self._load_strict_data_set()

        self.check_target()

    def test_single_click_changes_tab(self):
        self._load_strict_data_set()
        self._load_strict_data_set()

        second_stack_item = self.imaging.dataset_tree_widget.topLevelItem(1).child(0)
        second_stack_rect = self.imaging.dataset_tree_widget.visualItemRect(second_stack_item)
        QTest.mouseClick(self.imaging.dataset_tree_widget.viewport(), Qt.LeftButton, Qt.NoModifier,
                         second_stack_rect.center())

        self.check_target()

    def test_show_add_stack_to_existing_dataset_dialog_for_strict_dataset(self):
        self._load_strict_data_set()
        self.imaging.show_add_stack_to_existing_dataset_dialog(list(self.imaging.presenter.all_dataset_ids)[0])

        self.check_target(widget=self.imaging.add_to_dataset_dialog)

    def test_show_add_stack_to_existing_dataset_dialog_for_mixed_dataset(self):
        self._create_mixed_dataset()
        self.imaging.show_add_stack_to_existing_dataset_dialog(list(self.imaging.presenter.all_dataset_ids)[0])
        self.check_target(widget=self.imaging.add_to_dataset_dialog)

    def test_clicking_tab_changes_tree_view_selection(self):
        self._load_strict_data_set()
        sample_vis = self._load_strict_data_set()
        sample_vis.raise_()

        self.check_target()

    def test_move_stack_dialog_when_both_strict(self):
        sample_vis = self._load_strict_data_set()
        self._load_strict_data_set()

        self.imaging.presenter._set_tree_view_selection_with_id(sample_vis.id)

        self.imaging._move_stack()
        self.check_target(self.imaging.move_stack_dialog)

    def test_move_stack_dialog_strict_to_mixed(self):
        sample_vis = self._load_strict_data_set()
        mixed_ds = self._create_mixed_dataset()

        self.imaging.presenter._set_tree_view_selection_with_id(sample_vis.id)

        self.imaging._move_stack()
        self.imaging.move_stack_dialog.datasetSelector.setCurrentText(mixed_ds.name)
        self.check_target(self.imaging.move_stack_dialog)

    def test_move_stack_dialog_mixed_to_strict(self):
        mixed_ds = self._create_mixed_dataset()
        sample_vis = self._load_strict_data_set()
        strict_ds_id = self.imaging.presenter.model.get_parent_dataset(sample_vis.id)
        strict_ds = self.imaging.get_dataset(strict_ds_id)

        self.imaging.presenter._set_tree_view_selection_with_id(mixed_ds.all[0].id)

        self.imaging._move_stack()
        self.imaging.move_stack_dialog.datasetSelector.setCurrentText(strict_ds.name)
        self.check_target(self.imaging.move_stack_dialog)

    def test_move_stack_dialog_both_mixed(self):
        mixed_ds_1 = self._create_mixed_dataset()
        mixed_ds_2 = self._create_mixed_dataset()
        mixed_ds_2.name = "other-mixed-ds-name"

        self.imaging.presenter._set_tree_view_selection_with_id(mixed_ds_1.all[0].id)

        self.imaging._move_stack()
        self.imaging.move_stack_dialog.datasetSelector.setCurrentText(mixed_ds_2.name)
        self.check_target(self.imaging.move_stack_dialog)

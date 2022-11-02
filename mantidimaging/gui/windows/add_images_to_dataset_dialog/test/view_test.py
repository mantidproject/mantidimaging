# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from PyQt5.QtWidgets import QDialogButtonBox

from mantidimaging.gui.windows.add_images_to_dataset_dialog.presenter import Notification
from mantidimaging.gui.windows.add_images_to_dataset_dialog.view import AddImagesToDatasetDialog
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class AddImagesToDatasetDialogTest(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            self.main_window = MainWindowView()
        self.id = "dataset-id"
        self.dataset_name = "dataset-name"
        self.view = AddImagesToDatasetDialog(self.main_window, self.id, True, self.dataset_name)
        self.view.presenter = self.presenter = mock.MagicMock()

    def test_on_accepted(self):
        self.view._on_accepted()
        self.presenter.notify.assert_called_once_with(Notification.IMAGE_FILE_SELECTED)

    def test_label_contains_dataset_name(self):
        self.assertEqual(self.dataset_name, self.view.datasetNameText.text())

    def test_combo_box_enabled_for_strict_dataset(self):
        assert self.view.imageTypeComboBox.isEnabled()

    def test_combo_box_disabled_for_mixed_dataset(self):
        view = AddImagesToDatasetDialog(self.main_window, "id", False, "dataset-name")
        assert not view.imageTypeComboBox.isEnabled()

    def test_file_path_empty_and_ok_disabled_without_file_choice(self):
        assert not self.view.buttonBox.button(QDialogButtonBox.Ok).isEnabled()
        self.assertEqual(self.view.filePathLineEdit.text(), "")

    def test_file_choice_changes_line_edit_and_enables_ok_button(self):
        file_path = "file/path"
        with mock.patch("mantidimaging.gui.windows.add_images_to_dataset_dialog.view.QFileDialog.getOpenFileName"
                        ) as get_file_mock:
            get_file_mock.return_value = (file_path, None)
            self.view.choose_file_path()

        self.assertEqual(self.view.filePathLineEdit.text(), file_path)
        assert self.view.buttonBox.button(QDialogButtonBox.Ok).isEnabled()

    def test_path_returns_file_path_line_edit(self):
        test_path = "file/path"
        self.view.filePathLineEdit.setText(test_path)
        self.assertEqual(self.view.path, test_path)

    def test_images_type_returns_combo_box_value(self):
        combo_text = "Dark After"
        self.view.imageTypeComboBox.setCurrentText(combo_text)
        self.assertEqual(self.view.images_type, combo_text)

    def test_dataset_id_returns_id(self):
        self.assertEqual(self.view.dataset_id, self.id)

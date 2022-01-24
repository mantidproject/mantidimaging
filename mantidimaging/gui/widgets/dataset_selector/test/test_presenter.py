# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from mantidimaging.gui.widgets.dataset_selector.presenter import DatasetSelectorWidgetPresenter, Notification
from mantidimaging.gui.widgets.dataset_selector.view import DatasetSelectorWidgetView


class DatasetSelectorWidgetPresenterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.view = mock.create_autospec(DatasetSelectorWidgetView)
        self.presenter = DatasetSelectorWidgetPresenter(self.view)

    def test_handle_selection_no_matching_index_found(self):
        self.view.dataset_selected_uuid.emit = mock.Mock()
        self.presenter.handle_selection(1)
        self.view.dataset_selected_uuid.emit.assert_called_with(None)
        self.assertIsNone(self.presenter.current_dataset)

    def test_handle_selection_matching_index_found(self):
        matching_uuid = "second-uuid"
        self.presenter.dataset_uuids = ["first-uuid", matching_uuid]
        self.view.dataset_selected_uuid.emit = mock.Mock()

        self.presenter.handle_selection(1)
        self.view.dataset_selected_uuid.emit.assert_called_with(matching_uuid)
        assert matching_uuid == self.presenter.current_dataset

    def test_notify_reload_datasets(self):
        self.presenter.do_reload_datasets = mock.Mock()
        self.presenter.notify(Notification.RELOAD_DATASETS)
        self.presenter.do_reload_datasets.assert_called_once()

    def test_do_reload_datasets_keep_old_selection(self):
        self.view.main_window = mock.Mock()
        self.view.datasets_updated.emit = mock.Mock()
        self.view.dataset_selected_uuid.emit = mock.Mock()
        self.view.currentText.return_value = second_dataset_name = "second-dataset-name"
        first_dataset_name = "first-dataset-name"
        self.view.main_window.dataset_list = [("id-1", first_dataset_name), ("id-1", second_dataset_name)]
        self.presenter.do_reload_datasets()

        self.view.clear.assert_called_once()
        self.view.addItems.assert_called_once_with((
            first_dataset_name,
            second_dataset_name,
        ))
        self.view.setCurrentIndex.assert_called_once_with(1)
        self.view.datasets_updated.emit.assert_called_once()
        self.view.dataset_selected_uuid.emit.assert_called_once_with(self.presenter.dataset_uuids[1])
        assert self.presenter.current_dataset == self.presenter.dataset_uuids[1]

    def test_do_reload_datasets_no_old_selection(self):
        self.view.main_window = mock.Mock()
        self.view.datasets_updated.emit = mock.Mock()
        self.view.dataset_selected_uuid.emit = mock.Mock()
        self.view.currentText.return_value = "second-dataset-name"
        first_dataset_name = "first-dataset-name"
        self.view.main_window.dataset_list = [("id-1", first_dataset_name)]
        self.presenter.do_reload_datasets()

        self.view.clear.assert_called_once()
        self.view.addItems.assert_called_once_with((first_dataset_name, ))
        self.view.setCurrentIndex.assert_called_once_with(0)
        self.view.datasets_updated.emit.assert_called_once()
        self.view.dataset_selected_uuid.emit.assert_called_once_with(self.presenter.dataset_uuids[0])
        assert self.presenter.current_dataset == self.presenter.dataset_uuids[0]

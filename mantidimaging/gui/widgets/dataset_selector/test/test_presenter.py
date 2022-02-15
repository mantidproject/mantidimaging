# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from mantidimaging.core.data.dataset import StrictDataset, MixedDataset
from mantidimaging.gui.widgets.dataset_selector.presenter import DatasetSelectorWidgetPresenter, Notification
from mantidimaging.gui.widgets.dataset_selector.view import DatasetSelectorWidgetView


class DatasetSelectorWidgetPresenterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.view = mock.create_autospec(DatasetSelectorWidgetView)
        self.presenter = DatasetSelectorWidgetPresenter(self.view)

        self.view.main_window = mock.Mock()
        self.view.main_window.presenter = mock.Mock()

        self.img1 = mock.Mock(id="img1")
        self.img1.name = "Image 1"
        self.img1.proj180deg = None
        self.img2 = mock.Mock(id="img2")
        self.img2.name = "Image 2"
        self.img2.proj180deg = None
        self.img3 = mock.Mock(id="img3")
        self.img3.name = "Image 3"
        self.img4 = mock.Mock(id="img4")
        self.img4.name = "Image 4"
        self.ds1 = StrictDataset(sample=self.img1)
        self.ds1.name = "Dataset 1"
        self.ds2 = StrictDataset(sample=self.img2, flat_before=self.img3)
        self.ds2.name = "Dataset 2"
        self.ds3 = MixedDataset(stacks=[self.img4])
        self.ds3.name = "Dataset 3"

    def test_handle_selection_no_matching_index_found(self):
        self.view.dataset_selected_uuid.emit = mock.Mock()
        self.view.itemData = mock.Mock(return_value=None)
        self.presenter.handle_selection(1)
        self.view.dataset_selected_uuid.emit.assert_called_with(None)
        self.assertIsNone(self.presenter.current_dataset)

    def test_handle_selection_matching_index_found(self):
        matching_uuid = "second-uuid"
        self.view.dataset_selected_uuid.emit = mock.Mock()
        self.view.itemData = mock.Mock(return_value=matching_uuid)

        self.presenter.handle_selection(1)
        self.view.dataset_selected_uuid.emit.assert_called_with(matching_uuid)
        assert matching_uuid == self.presenter.current_dataset

    def test_notify_reload_datasets(self):
        self.presenter.do_reload_datasets = mock.Mock()
        self.presenter.notify(Notification.RELOAD_DATASETS)
        self.presenter.do_reload_datasets.assert_called_once()

    def test_do_reload_datasets_keep_old_selection(self):
        self.view.main_window.presenter.datasets = [self.ds1, self.ds2]
        self.view.datasets_updated.emit = mock.Mock()
        self.view.dataset_selected_uuid.emit = mock.Mock()
        self.view.itemData = mock.Mock(return_value=self.ds2.id)
        self.view.currentText.return_value = self.ds2.name

        self.presenter.do_reload_datasets()

        self.view.clear.assert_called_once()
        self.assertEqual(self.view.addItem.call_count, 2)
        self.view.addItem.assert_any_call(self.ds1.name, self.ds1.id)
        self.view.addItem.assert_any_call(self.ds2.name, self.ds2.id)
        self.view.setCurrentIndex.assert_called_once_with(1)
        self.view.datasets_updated.emit.assert_called_once()
        self.view.dataset_selected_uuid.emit.assert_called_once_with(self.ds2.id)
        assert self.presenter.current_dataset == self.ds2.id

    def test_do_reload_datasets_no_old_selection(self):
        self.view.main_window.presenter.datasets = [self.ds1]
        self.view.datasets_updated.emit = mock.Mock()
        self.view.dataset_selected_uuid.emit = mock.Mock()
        self.view.itemData = mock.Mock(return_value=self.ds1.id)
        self.view.currentText.return_value = self.ds2.name

        self.presenter.do_reload_datasets()

        self.view.clear.assert_called_once()
        self.assertEqual(self.view.addItem.call_count, 1)
        self.view.addItem.assert_any_call(self.ds1.name, self.ds1.id)
        self.view.setCurrentIndex.assert_called_once_with(0)
        self.view.datasets_updated.emit.assert_called_once()
        self.view.dataset_selected_uuid.emit.assert_called_once_with(self.ds1.id)
        assert self.presenter.current_dataset == self.ds1.id

    def test_do_reload_datasets_stacks(self):
        self.view.main_window.presenter.datasets = [self.ds1, self.ds2, self.ds3]
        self.presenter.show_stacks = True
        self.view.datasets_updated.emit = mock.Mock()
        self.view.stack_selected_uuid.emit = mock.Mock()

        self.presenter.do_reload_datasets()
        self.assertEqual(self.view.addItem.call_count, 4)
        self.view.addItem.assert_any_call(self.img1.name, self.img1.id)
        self.view.addItem.assert_any_call(self.img2.name, self.img2.id)
        self.view.addItem.assert_any_call(self.img3.name, self.img3.id)
        self.view.addItem.assert_any_call(self.img4.name, self.img4.id)

    def test_do_reload_datasets_by_dataset_type(self):
        self.view.main_window.presenter.datasets = [self.ds1, self.ds2, self.ds3]
        self.presenter.show_stacks = True
        self.presenter.relevant_dataset_types = StrictDataset
        self.view.datasets_updated.emit = mock.Mock()
        self.view.stack_selected_uuid.emit = mock.Mock()

        self.presenter.do_reload_datasets()
        self.assertEqual(self.view.addItem.call_count, 3)
        self.view.addItem.assert_any_call(self.img1.name, self.img1.id)
        self.view.addItem.assert_any_call(self.img2.name, self.img2.id)
        self.view.addItem.assert_any_call(self.img3.name, self.img3.id)

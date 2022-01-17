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

    def test_do_reload_datasets(self):
        self.view.main_window = mock.Mock()
        self.view.datasets_updated.emit = mock.Mock()
        self.view.dataset_selected_uuid.emit = mock.Mock()
        self.view.currentText.return_value = dataset_name = "dataset-name"
        self.view.main_window.dataset_list = [("dataset-id", dataset_name)]
        self.presenter.do_reload_datasets()

import unittest
from unittest import mock

from mantidimaging.gui.widgets.dataset_selector.presenter import DatasetSelectorWidgetPresenter
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

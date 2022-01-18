import unittest
from unittest import mock

from mantidimaging.gui.widgets.dataset_selector.presenter import Notification
from mantidimaging.gui.widgets.dataset_selector.view import DatasetSelectorWidgetView
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class DatasetSelectorWidgetViewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.view = DatasetSelectorWidgetView(None)

    def test_subscribe_to_main_window(self):
        main_window_mock = mock.create_autospec(MainWindowView)
        main_window_mock.model_changed.connect = mock.Mock()
        self.view.presenter = presenter_mock = mock.Mock()

        self.view.subscribe_to_main_window(main_window_mock)
        presenter_mock.notify.assert_called_once_with(Notification.RELOAD_DATASETS)
        main_window_mock.model_changed.connect.assert_called_once_with(self.view._handle_loaded_datasets_changed)
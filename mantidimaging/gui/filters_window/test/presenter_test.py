import unittest

from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.filters_window import (
        FiltersWindowPresenter, FiltersWindowView)
from mantidimaging.gui.main_window import MainWindowView

mock = import_mock()


class FiltersWindowPresenterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FiltersWindowPresenterTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.main_window = mock.create_autospec(MainWindowView)
        self.view = mock.create_autospec(FiltersWindowView)
        self.presenter = FiltersWindowPresenter(self.view, self.main_window)

    def test_show_error_message_forwarded_to_view(self):
        self.presenter.show_error("test message")
        self.view.show_error_dialog.assert_called_once_with("test message")


if __name__ == '__main__':
    unittest.main()

import unittest

import numpy as np

import mantidimaging.tests.test_helper as th

from mantidimaging.gui.main_window.mw_presenter import MainWindowPresenter
from mantidimaging.gui.main_window.mw_view import MainWindowView

mock = th.import_mock()


class MainWindowPresenterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MainWindowPresenterTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.config = None
        self.view = mock.create_autospec(MainWindowView)
        self.presenter = MainWindowPresenter(self.view, self.config)

    def test_show_error_message_forwarded_to_view(self):
        self.presenter.show_error("test message")
        self.view.show_error_dialog.assert_called_once_with("test message")


if __name__ == '__main__':
    unittest.main()

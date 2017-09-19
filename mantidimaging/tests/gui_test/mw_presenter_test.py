import sys
import unittest

if sys.version_info >= (3, 3):
    # Use unittest.mock on Python 3.3 and above
    import unittest.mock as mock

    if sys.version_info < (3, 6):
        # If on Python 3.5 and below then need to monkey patch this function in
        # It is available as standard on Python 3.6 and above
        def assert_called_once(_mock_self):
            self = _mock_self
            if not self.call_count == 1:
                msg = ("Expected '%s' to have been called once. Called %s times." %
                        (self._mock_name or 'mock', self.call_count))
                raise AssertionError(msg)
        unittest.mock.Mock.assert_called_once = assert_called_once
else:
    # Use mock on Python < 3.3
    import mock

import numpy as np

import mantidimaging.tests.test_helper as th

from mantidimaging.gui.main_window.mw_presenter import MainWindowPresenter
from mantidimaging.gui.main_window.mw_view import MainWindowView


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

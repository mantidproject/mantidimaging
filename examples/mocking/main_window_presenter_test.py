from __future__ import absolute_import, division, print_function

import unittest

import mock

import main_window_presenter
import main_window_view_abs
"""
you can comment out a line in the presenter, and the test should fail here
otherwise it's not being properly tested
"""


class MainWindowPresenterTest(unittest.TestCase):
    def setUp(self):
        # create the mock that has all functions from the abstract class
        # but they only return None and do nothing
        self.view = mock.create_autospec(
            main_window_view_abs.ImgpyMainWindowView)

        # initialise our presenter with the view
        self.presenter = main_window_presenter.ImgpyMainWindowPresenter(
            self.view)

    def test_get_and_set_value(self):
        # we have to do this if the function is expected to return something
        self.view.get_value = mock.Mock(return_value=5)

        # notify the presenter, as the view would do IRL
        self.presenter.notify(
            main_window_presenter.Notification.RESET_VALUE_CLICKED)

        # expect a SINGLE call, if called 0 times or twice it will fail
        self.view.set_value.assert_called_once_with(5)

    def test_set_value(self):
        # but not here because the default return is None anyway
        # self.view.get_value = mock.Mock(return_value=None)
        # notify the presenter, as the view would do IRL
        self.presenter.notify(main_window_presenter.Notification.SET_VALUE)
        self.view.set_value.assert_called_once_with(5)


if __name__ == '__main__':
    unittest.main()

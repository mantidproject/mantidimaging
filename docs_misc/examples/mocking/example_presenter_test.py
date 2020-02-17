import unittest

import mock

import example_presenter
import example_view_abs
"""
you can comment out a line in the presenter, and the test should fail here
otherwise it's not being properly tested
"""


class ExamplePresenterTest(unittest.TestCase):
    def setUp(self):
        # create the mock that has all functions from the abstract class
        # but they only return None and do nothing
        self.view = mock.create_autospec(example_view_abs.ImgpyExampleView)

        # initialise our presenter with the view
        self.presenter = example_presenter.ImgpyExamplePresenter(self.view)

    def test_get_and_set_value(self):
        # we have to do this if the function is expected to return something
        self.view.get_value = mock.Mock(return_value=5)

        # notify the presenter, as the view would do IRL
        self.presenter.notify(example_presenter.Notification.RESET_VALUE_CLICKED)

        # expect a SINGLE call, if called 0 times or twice it will fail
        self.view.set_value.assert_called_once_with(5)

    def test_set_value(self):
        # but not here because the default return is None anyway
        # self.view.get_value = mock.Mock(return_value=None)
        # notify the presenter, as the view would do IRL
        self.presenter.notify(example_presenter.Notification.SET_VALUE)
        self.view.set_value.assert_called_once_with(5)


if __name__ == '__main__':
    unittest.main()

import unittest

from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.async_task_dialog import TaskWorkerThread
from mantidimaging.gui.main_window.load_dialog import MWLoadDialog
from mantidimaging.gui.main_window.mw_presenter import MainWindowPresenter
from mantidimaging.gui.main_window.mw_view import MainWindowView

mock = import_mock()


class MainWindowPresenterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MainWindowPresenterTest, self).__init__(*args, **kwargs)

    def setUp(self):
        super(MainWindowPresenterTest, self).setUp()

        self.config = None
        self.view = mock.create_autospec(MainWindowView)
        self.view.load_dialogue = mock.create_autospec(MWLoadDialog)
        self.presenter = MainWindowPresenter(self.view, self.config)

    def test_show_error_message_forwarded_to_view(self):
        self.presenter.show_error("test message")
        self.view.show_error_dialog.assert_called_once_with("test message")

    def test_failed_attempt_to_load_shows_error(self):
        # Create a filed load async task
        task = TaskWorkerThread()
        task.error = 'something'
        self.assertFalse(task.was_successful())

        # Call the callback with a task that failed
        self.presenter._on_stack_load_done(task)

        # Expect error message
        self.view.show_error_dialog.assert_called_once_with(
                "Failed to load stack. See log for details.")

    def test_failed_attempt_to_save_shows_error(self):
        # Create a filed load async task
        task = TaskWorkerThread()
        task.error = 'something'
        self.assertFalse(task.was_successful())

        # Call the callback with a task that failed
        self.presenter._on_save_done(task)

        # Expect error message
        self.view.show_error_dialog.assert_called_once_with(
                "Failed to save stack. See log for details.")


if __name__ == '__main__':
    unittest.main()

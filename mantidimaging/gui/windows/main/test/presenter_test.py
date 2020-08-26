import unittest

import mock

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.gui.dialogs.async_task import TaskWorkerThread
from mantidimaging.gui.windows.main import MainWindowView, MainWindowPresenter
from mantidimaging.gui.windows.load_dialog import MWLoadDialog
from mantidimaging.test_helpers.unit_test_helper import generate_images


class MainWindowPresenterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MainWindowPresenterTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.view = mock.create_autospec(MainWindowView)
        self.view.load_dialogue = mock.create_autospec(MWLoadDialog)
        self.presenter = MainWindowPresenter(self.view)

    def test_failed_attempt_to_load_shows_error(self):
        # Create a filed load async task
        task = TaskWorkerThread()
        task.error = 'something'
        self.assertFalse(task.was_successful())

        # Call the callback with a task that failed
        self.presenter._on_stack_load_done(task)

        # Expect error message
        self.view.show_error_dialog.assert_called_once_with(self.presenter.LOAD_ERROR_STRING.format(task.error))

    def test_failed_attempt_to_save_shows_error(self):
        # Create a filed load async task
        task = TaskWorkerThread()
        task.error = 'something'
        self.assertFalse(task.was_successful())

        # Call the callback with a task that failed
        self.presenter._on_save_done(task)

        # Expect error message
        self.view.show_error_dialog.assert_called_once_with(self.presenter.SAVE_ERROR_STRING.format(task.error))

    @mock.patch("mantidimaging.gui.windows.main.presenter.start_async_task_view")
    def test_load_stack(self, start_async_mock: mock.Mock):
        parameters_mock = mock.Mock()
        parameters_mock.sample.input_path.return_value = "123"
        self.view.load_dialogue.get_parameters.return_value = parameters_mock

        self.presenter.load_stack()

        start_async_mock.assert_called_once_with(self.view, self.presenter.model.do_load_stack,
                                                 self.presenter._on_stack_load_done, {'parameters': parameters_mock})

    def test_make_stack_window(self):
        images = generate_images()
        dock_mock = mock.Mock()
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        self.view._create_stack_window.return_value = dock_mock

        dock, sv = self.presenter._make_stack_window(images, "mytitle")

        self.assertIs(dock_mock, dock)
        self.assertIs(stack_visualiser_mock, sv)

    def test_add_stack(self):
        images = generate_images()
        dock_mock = mock.Mock()
        sample_dock_mock = mock.Mock()
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        self.view._create_stack_window.return_value = dock_mock

        self.presenter._add_stack(images, "myfilename", sample_dock_mock)

        self.assertEqual(1, len(self.presenter.model.stack_list))
        self.view.tabifyDockWidget.assert_called_once_with(sample_dock_mock, dock_mock)

    def test_create_new_stack_images(self):
        self.view.active_stacks_changed.emit = mock.Mock()
        images = generate_images()
        self.presenter.create_new_stack(images, "My title")
        self.assertEqual(1, len(self.presenter.model.stack_list))
        self.view.active_stacks_changed.emit.assert_called_once()

    def test_create_new_stack_dataset(self):
        dock_mock = mock.Mock()
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        dock_mock.windowTitle.return_value = "somename"
        self.view._create_stack_window.return_value = dock_mock
        self.view.active_stacks_changed.emit = mock.Mock()

        ds = Dataset(sample=generate_images(automatic_free=False),
                     flat=generate_images(automatic_free=False),
                     dark=generate_images(automatic_free=False))
        ds.flat.filenames = ["filename"] * 10
        ds.dark.filenames = ["filename"] * 10

        self.presenter.create_new_stack(ds, "My title")

        self.assertEqual(3, len(self.presenter.model.stack_list))
        self.view.active_stacks_changed.emit.assert_called_once()

        ds.sample.free_memory()
        ds.flat.free_memory()
        ds.dark.free_memory()


if __name__ == '__main__':
    unittest.main()

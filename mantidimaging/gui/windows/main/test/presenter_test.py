# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from unittest import mock

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.gui.dialogs.async_task import TaskWorkerThread
from mantidimaging.gui.windows.load_dialog import MWLoadDialog
from mantidimaging.gui.windows.main import MainWindowView, MainWindowPresenter
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
    def test_dataset_stack(self, start_async_mock: mock.Mock):
        parameters_mock = mock.Mock()
        parameters_mock.sample.input_path.return_value = "123"
        self.view.load_dialogue.get_parameters.return_value = parameters_mock

        self.presenter.load_dataset()

        start_async_mock.assert_called_once_with(self.view, self.presenter.model.do_load_stack,
                                                 self.presenter._on_dataset_load_done, {'parameters': parameters_mock})

    @mock.patch("mantidimaging.gui.windows.main.presenter.start_async_task_view")
    def test_load_stack(self, start_async_mock: mock.Mock):
        file_path = mock.Mock()

        self.presenter.load_image_stack(file_path)

        start_async_mock.assert_called_once_with(self.view, self.presenter.model.load_stack,
                                                 self.presenter._on_stack_load_done, {'file_path': file_path})

    def test_make_stack_window(self):
        images = generate_images()
        dock_mock = mock.Mock()
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        self.view.create_stack_window.return_value = dock_mock

        dock, sv = self.presenter.make_stack_window(images, "mytitle")

        self.assertIs(dock_mock, dock)
        self.assertIs(stack_visualiser_mock, sv)

    def test_add_stack(self):
        images = generate_images()
        dock_mock = mock.Mock()
        sample_dock_mock = mock.Mock()
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        self.view.create_stack_window.return_value = dock_mock

        self.presenter._add_stack(images, "myfilename", sample_dock_mock)

        self.assertEqual(1, len(self.presenter.model.stack_list))
        self.view.tabifyDockWidget.assert_called_once_with(sample_dock_mock, dock_mock)

    def test_add_multiple_stacks(self):
        images = generate_images()
        images2 = generate_images()
        dock_mock = mock.Mock()
        sample_dock_mock = mock.Mock()
        stack_visualiser_mock = mock.Mock()
        self.presenter.model = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        self.view.create_stack_window.return_value = dock_mock

        self.presenter._add_stack(images, "myfilename", sample_dock_mock)
        self.presenter._add_stack(images2, "myfilename2", sample_dock_mock)

        self.assertEqual(2, self.presenter.model.add_stack.call_count)
        self.view.tabifyDockWidget.assert_called_with(sample_dock_mock, dock_mock)
        self.assertEqual(2, self.view.tabifyDockWidget.call_count)

    def test_create_new_stack_images(self):
        self.view.active_stacks_changed.emit = mock.Mock()
        images = generate_images()
        self.presenter.create_new_stack(images, "My title")
        self.assertEqual(1, len(self.presenter.model.stack_list))
        self.view.active_stacks_changed.emit.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.main.presenter.QApplication")
    def test_create_new_stack_images_focuses_newest_tab(self, mock_QApp):
        self.view.active_stacks_changed.emit = mock.Mock()
        images = generate_images()
        self.presenter.create_new_stack(images, "My title")
        self.assertEqual(1, len(self.presenter.model.stack_list))
        self.view.active_stacks_changed.emit.assert_called_once()

        self.presenter.create_new_stack(images, "My title")
        self.view.tabifyDockWidget.assert_called_once()
        self.view.findChild.assert_called_once()
        mock_tab_bar = self.view.findChild.return_value
        expected_position = 1
        mock_tab_bar.setCurrentIndex.assert_called_once_with(expected_position)
        mock_QApp.sendPostedEvents.assert_called_once()

    def test_create_new_stack_dataset(self):
        dock_mock = mock.Mock()
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        dock_mock.windowTitle.return_value = "somename"
        self.view.create_stack_window.return_value = dock_mock
        self.view.active_stacks_changed.emit = mock.Mock()

        ds = Dataset(sample=generate_images(),
                     flat_before=generate_images(),
                     flat_after=generate_images(),
                     dark_before=generate_images(),
                     dark_after=generate_images())
        ds.flat_before.filenames = ["filename"] * 10
        ds.dark_before.filenames = ["filename"] * 10
        ds.flat_after.filenames = ["filename"] * 10
        ds.dark_after.filenames = ["filename"] * 10

        self.presenter.create_new_stack(ds, "My title")

        self.assertEqual(5, len(self.presenter.model.stack_list))
        self.view.active_stacks_changed.emit.assert_called_once()


if __name__ == '__main__':
    unittest.main()

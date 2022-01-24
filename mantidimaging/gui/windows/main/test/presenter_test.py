# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
import uuid
from typing import List

from unittest import mock

import numpy as np

from mantidimaging.core.data.dataset import Dataset, StackDataset
from mantidimaging.core.utility.data_containers import ProjectionAngles
from mantidimaging.gui.dialogs.async_task import TaskWorkerThread
from mantidimaging.gui.windows.load_dialog import MWLoadDialog
from mantidimaging.gui.windows.main import MainWindowView, MainWindowPresenter
from mantidimaging.gui.windows.main.presenter import Notification
from mantidimaging.test_helpers.unit_test_helper import generate_images


class MainWindowPresenterTest(unittest.TestCase):
    def setUp(self):
        self.view = mock.create_autospec(MainWindowView)
        self.view.load_dialogue = mock.create_autospec(MWLoadDialog)
        self.presenter = MainWindowPresenter(self.view)
        self.images = [generate_images() for _ in range(5)]
        self.dataset = Dataset(sample=self.images[0],
                               flat_before=self.images[1],
                               flat_after=self.images[2],
                               dark_before=self.images[3],
                               dark_after=self.images[4])
        self.presenter.model = self.model = mock.Mock()

        self.view.create_stack_window.return_value = dock_mock = mock.Mock()
        self.view.model_changed = mock.Mock()
        self.view.dataset_tree_widget = mock.Mock()

        def stack_id():
            return uuid.uuid4()

        type(dock_mock).uuid = mock.PropertyMock(side_effect=stack_id)

    def tearDown(self) -> None:
        self.presenter.stack_visualisers = []

    def create_mock_stacks_with_names(self, stack_names: List[str]):
        stacks = dict()
        for name in stack_names:
            stack_mock = mock.Mock()
            stack_mock.windowTitle.return_value = name
            stacks[uuid.uuid4()] = stack_mock
        self.presenter.stack_visualisers = stacks

    def test_initial_stack_list(self):
        self.assertEqual(self.presenter.stack_visualiser_names, [])

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

        start_async_mock.assert_called_once_with(self.view, self.presenter.model.do_load_dataset,
                                                 self.presenter._on_dataset_load_done, {'parameters': parameters_mock})

    @mock.patch("mantidimaging.gui.windows.main.presenter.start_async_task_view")
    def test_load_dataset_returns_when_par_and_view_dialog_are_none(self, start_async_mock: mock.Mock):
        self.view.load_dialogue = None
        self.presenter.load_dataset()

        start_async_mock.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.main.presenter.start_async_task_view")
    def test_load_stack(self, start_async_mock: mock.Mock):
        file_path = mock.Mock()

        self.presenter.load_image_stack(file_path)

        start_async_mock.assert_called_once_with(self.view, self.presenter.model.load_images,
                                                 self.presenter._on_stack_load_done, {'file_path': file_path})

    def test_add_stack(self):
        images = generate_images()
        dock_mock = mock.Mock()
        sample_dock_mock = mock.Mock()
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        self.view.create_stack_window.return_value = dock_mock

        self.presenter._add_stack(images, sample_dock_mock)

        self.assertEqual(1, len(self.presenter.stack_visualiser_list))
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

        self.presenter._add_stack(images, sample_dock_mock)
        self.presenter._add_stack(images2, sample_dock_mock)

        self.assertEqual(2, self.view.create_stack_window.call_count)
        self.view.tabifyDockWidget.assert_called_with(sample_dock_mock, dock_mock)
        self.assertEqual(2, self.view.tabifyDockWidget.call_count)

    def test_create_new_stack_images(self):
        self.view.model_changed.emit = mock.Mock()
        images = generate_images()
        self.presenter.create_new_stack(images)
        self.assertEqual(1, len(self.presenter.stack_visualisers))
        self.view.model_changed.emit.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.main.presenter.QApplication")
    def test_create_new_stack_images_focuses_newest_tab(self, mock_QApp):
        first_images = generate_images()
        second_images = generate_images()

        first_stack_window = mock.Mock()
        second_stack_window = mock.Mock()

        first_stack_window.id = first_images.id
        second_stack_window.id = second_images.id

        self.view.create_stack_window.side_effect = [first_stack_window, second_stack_window]

        self.view.model_changed.emit = mock.Mock()
        self.presenter.create_new_stack(first_images)
        self.assertEqual(1, len(self.presenter.stack_visualisers))
        self.view.model_changed.emit.assert_called_once()

        self.presenter.create_new_stack(second_images)
        assert self.view.tabifyDockWidget.call_count == 2
        assert self.view.findChild.call_count == 1
        mock_tab_bar = self.view.findChild.return_value
        expected_position = 2
        mock_tab_bar.setCurrentIndex.assert_called_once_with(expected_position)
        mock_QApp.sendPostedEvents.assert_called_once()

    def test_create_new_stack_with_180_in_sample(self):
        dock_mock = self.view.create_stack_window.return_value
        stack_visualiser_mock = mock.Mock()
        self.dataset.sample.proj180deg = generate_images(shape=(1, 20, 20))
        self.dataset.sample.proj180deg.filenames = ["filename"]

        dock_mock.widget.return_value = stack_visualiser_mock
        dock_mock.windowTitle.return_value = "somename"
        self.view.model_changed.emit = mock.Mock()

        self.dataset.flat_before.filenames = ["filename"] * 10
        self.dataset.dark_before.filenames = ["filename"] * 10
        self.dataset.flat_after.filenames = ["filename"] * 10
        self.dataset.dark_after.filenames = ["filename"] * 10

        self.presenter.create_new_stack(self.dataset)

        self.assertEqual(6, len(self.presenter.stack_visualisers))
        self.view.model_changed.emit.assert_called_once()

    def test_create_new_stack_dataset_and_use_threshold_180(self):
        dock_mock = self.view.create_stack_window.return_value
        stack_visualiser_mock = mock.Mock()
        self.dataset.sample.set_projection_angles(
            ProjectionAngles(np.linspace(0, np.pi, self.dataset.sample.num_images)))

        dock_mock.widget.return_value = stack_visualiser_mock
        dock_mock.windowTitle.return_value = "somename"
        self.view.model_changed.emit = mock.Mock()

        self.dataset.flat_before.filenames = ["filename"] * 10
        self.dataset.dark_before.filenames = ["filename"] * 10
        self.dataset.flat_after.filenames = ["filename"] * 10
        self.dataset.dark_after.filenames = ["filename"] * 10

        self.view.ask_to_use_closest_to_180.return_value = False

        self.presenter.create_new_stack(self.dataset)

        self.assertEqual(6, len(self.presenter.stack_visualisers))
        self.view.model_changed.emit.assert_called_once()

    def test_create_new_stack_dataset_and_reject_180(self):
        dock_mock = self.view.create_stack_window.return_value
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        dock_mock.windowTitle.return_value = "somename"
        self.view.model_changed.emit = mock.Mock()

        self.dataset.flat_before.filenames = ["filename"] * 10
        self.dataset.dark_before.filenames = ["filename"] * 10
        self.dataset.flat_after.filenames = ["filename"] * 10
        self.dataset.dark_after.filenames = ["filename"] * 10

        self.view.ask_to_use_closest_to_180.return_value = False

        self.presenter.create_new_stack(self.dataset)

        self.assertEqual(5, len(self.presenter.stack_visualisers))
        self.view.model_changed.emit.assert_called_once()

    def test_create_new_stack_dataset_and_accept_180(self):
        dock_mock = self.view.create_stack_window.return_value
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        dock_mock.windowTitle.return_value = "somename"
        self.view.model_changed.emit = mock.Mock()

        self.dataset.flat_before.filenames = ["filename"] * 10
        self.dataset.dark_before.filenames = ["filename"] * 10
        self.dataset.flat_after.filenames = ["filename"] * 10
        self.dataset.dark_after.filenames = ["filename"] * 10

        self.view.ask_to_use_closest_to_180.return_value = True

        self.presenter.create_new_stack(self.dataset)

        self.assertEqual(6, len(self.presenter.stack_visualisers))
        self.view.model_changed.emit.assert_called_once()

    def test_wizard_action_load(self):
        self.presenter.wizard_action_load()
        self.view.show_load_dialogue.assert_called_once()

    def test_wizard_action_show_operation(self):
        OPERATION_STR = "ROI Normalisation"
        self.presenter.show_operation(OPERATION_STR)
        self.view.show_filters_window.assert_called_once()
        self.view.filters.presenter.set_filter_by_name.assert_called_once_with(OPERATION_STR)

    def test_wizard_action_show_reconstruction(self):
        self.presenter.wizard_action_show_reconstruction()
        self.view.show_recon_window.assert_called_once()

    def test_nexus_load_success_calls_show_information(self):
        self.view.nexus_load_dialog = mock.Mock()
        data_title = "data tile"
        self.view.nexus_load_dialog.presenter.get_dataset.return_value = self.dataset, data_title
        self.presenter.create_new_stack = mock.Mock()
        self.presenter.load_nexus_file()
        self.presenter.create_new_stack.assert_called_once_with(self.dataset)

    def test_get_stack_widget_by_name_success(self):
        stack_window = mock.Mock()
        stack_window.id = "id"
        stack_window.isVisible.return_value = True
        stack_window.windowTitle.return_value = stack_window_title = "stack window title"
        self.presenter.stack_visualisers[stack_window.id] = stack_window

        self.assertIs(stack_window, self.presenter._get_stack_visualiser_by_name(stack_window_title))

    def test_get_stack_widget_by_name_failure(self):
        self.assertIsNone(self.presenter._get_stack_visualiser_by_name("doesn't exist"))

    def test_get_stack_id_by_name_success(self):
        stack_window = mock.Mock()
        stack_window.id = stack_id = "id"
        stack_window.isVisible.return_value = True
        stack_window.windowTitle.return_value = stack_window_title = "stack window title"
        self.presenter.stack_visualisers[stack_window.id] = stack_window

        self.assertIs(stack_id, self.presenter.get_stack_id_by_name(stack_window_title))

    def test_get_stack_id_by_name_failure(self):
        self.assertIsNone(self.presenter._get_stack_visualiser_by_name("bad-id"))

    def test_add_log_to_sample_success(self):
        stack_window = mock.Mock()
        stack_window.id = stack_id = "id"
        stack_window.isVisible.return_value = True
        stack_window.windowTitle.return_value = stack_window_title = "stack window title"
        self.presenter.stack_visualisers[stack_window.id] = stack_window
        log_file = "log file"

        self.presenter.add_log_to_sample(stack_window_title, log_file)
        self.model.add_log_to_sample.assert_called_once_with(stack_id, log_file)

    def test_add_log_to_sample_failure(self):
        with self.assertRaises(RuntimeError):
            self.presenter.add_log_to_sample("doesn't exist", "log file")

    def test_do_rename_stack(self):
        self.presenter.stack_visualisers["stack-id"] = mock_stack = mock.Mock()
        mock_stack.windowTitle.return_value = previous_title = "previous title"
        new_title = "new title"
        self.presenter._do_rename_stack(previous_title, new_title)
        mock_stack.setWindowTitle.assert_called_once_with(new_title)
        self.view.model_changed.emit.assert_called_once()

    def test_create_new_180_stack_with_multiple_visible_stacks(self):
        stacks = dict()
        for _ in range(3):
            stack = mock.Mock()
            stack.isVisible.return_value = True
            stacks[uuid.uuid4()] = stack

        self.presenter.stack_visualisers = stacks
        self.view.create_stack_window.return_value = stack_vis_180 = mock.Mock()
        self.view.findChild.return_value = tab_bar_mock = mock.Mock()

        images_180 = generate_images()

        self.assertIs(self.presenter.create_new_180_stack(images_180), stack_vis_180)
        self.view.tabifyDockWidget.assert_called_once()
        self.view.model_changed.emit.assert_called_once()
        tab_bar_mock.setCurrentIndex.assert_called_once_with(3)

    def test_create_new_180_stack_with_no_visible_stacks(self):
        stacks = dict()
        for _ in range(3):
            stack = mock.Mock()
            stack.isVisible.return_value = False
            stacks[uuid.uuid4()] = stack

        self.presenter.stack_visualisers = stacks
        self.view.create_stack_window.return_value = stack_vis_180 = mock.Mock()

        images_180 = generate_images()

        self.assertIs(self.presenter.create_new_180_stack(images_180), stack_vis_180)
        self.view.tabifyDockWidget.assert_not_called()
        self.view.model_changed.emit.assert_called_once()
        self.view.findChild.assert_not_called()

    def test_get_stack_visualiser_success(self):
        stack_id = "stack-id"
        stack_mock = mock.Mock()
        self.presenter.stack_visualisers[stack_id] = stack_mock
        self.assertIs(self.presenter.get_stack_visualiser(stack_id), stack_mock)

    def test_get_stack_names(self):
        stack_names = [f"window title {str(i)}" for i in range(5)]
        self.create_mock_stacks_with_names(stack_names)
        self.assertListEqual(self.presenter.stack_visualiser_names, stack_names)

    def test_get_stack_with_images_success(self):
        mock_stack = mock.Mock()
        mock_stack.presenter.images = images = generate_images()
        self.presenter.stack_visualisers[images.id] = mock_stack

        self.assertEqual(self.presenter.get_stack_with_images(images), mock_stack)

    def test_get_stack_with_images_failure(self):
        with self.assertRaises(RuntimeError):
            self.presenter.get_stack_with_images(generate_images())

    def test_set_images_in_stack(self):
        mock_stack = mock.Mock()
        mock_stack.presenter.images = old_images = generate_images()
        self.presenter.stack_visualisers[old_images.id] = mock_stack
        new_images = generate_images()

        self.presenter.set_images_in_stack(old_images.id, new_images)
        mock_stack.image_view.clear.assert_called_once()
        mock_stack.image_view.setImage.assert_called_once_with(new_images.data)
        self.assertEqual(self.presenter.stack_visualisers[old_images.id].presenter.images, new_images)

    def test_set_same_image_in_stack(self):
        mock_stack = mock.Mock()
        mock_stack.presenter.images = old_images = generate_images()
        self.presenter.stack_visualisers[old_images.id] = mock_stack

        self.presenter.set_images_in_stack(old_images.id, old_images)
        mock_stack.image_view.clear.assert_not_called()
        mock_stack.image_view.setImage.assert_not_called()
        self.assertEqual(self.presenter.stack_visualisers[old_images.id].presenter.images, old_images)

    def test_add_180_deg_to_dataset_success(self):
        dataset_id = "dataset-id"
        filename_for_180 = "path/to/180"
        self.model.add_180_deg_to_dataset.return_value = _180_deg = generate_images((1, 200, 200))
        self.presenter.add_child_item_to_tree_view = mock.Mock()

        self.presenter.add_180_deg_to_dataset(dataset_id, filename_for_180)
        self.model.add_180_deg_to_dataset.assert_called_once_with(dataset_id, filename_for_180)
        self.presenter.add_child_item_to_tree_view.assert_called_once_with(dataset_id, _180_deg.id, "180")

    def test_add_180_deg_to_dataset_failure(self):
        self.model.add_180_deg_to_dataset.return_value = None
        self.assertIsNone(self.presenter.add_180_deg_to_dataset("doesn't-exist", "path/to/180"))

    def test_add_projection_angles_to_stack_success(self):
        mock_stack = mock.Mock()
        mock_stack.windowTitle.return_value = window_title = "window title"
        stack_id = "stack-id"
        self.presenter.stack_visualisers[stack_id] = mock_stack
        projection_angles = ProjectionAngles(np.ndarray([1]))

        self.presenter.add_projection_angles_to_sample(window_title, projection_angles)
        self.model.add_projection_angles_to_sample(stack_id, projection_angles)

    def test_add_projection_angles_to_stack_failure(self):
        with self.assertRaises(RuntimeError):
            self.presenter.add_projection_angles_to_sample("doesn't-exist", ProjectionAngles(np.ndarray([1])))
        self.model.add_projection_angles_to_sample.assert_not_called()

    def test_remove_dataset_from_tree_view(self):
        """
        Removing an ID that corresponds with a top-level item means a dataset is being removed.
        """
        top_level_item_mock = mock.Mock()
        top_level_item_mock.id = stack_id = "stack-id"
        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        self.view.dataset_tree_widget.topLevelItem.return_value = top_level_item_mock

        self.presenter.remove_item_from_tree_view(stack_id)
        self.view.dataset_tree_widget.takeTopLevelItem.assert_called_once_with(0)

    def test_remove_images_from_tree_view(self):
        """
        Removing an ID that corresponds with a child-item means an image stack is being removed.
        """
        top_level_item_mock = mock.Mock()
        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        self.view.dataset_tree_widget.topLevelItem.return_value = top_level_item_mock
        top_level_item_mock.childCount.return_value = 1
        top_level_item_mock.child.return_value = child_item_mock = mock.Mock()
        child_item_mock.id = stack_id = "stack-id"

        self.presenter.remove_item_from_tree_view(stack_id)
        top_level_item_mock.takeChild.assert_called_once_with(0)

    def test_have_active_stacks_true(self):
        mock_stack = mock.Mock()
        mock_stack.isVisible.return_value = True
        self.presenter.stack_visualisers = {"stack-id": mock_stack}
        self.assertTrue(self.presenter.have_active_stacks)

    def test_have_active_stacks_false(self):
        mock_stack = mock.Mock()
        mock_stack.isVisible.return_value = False
        self.presenter.stack_visualisers = {"stack-id": mock_stack}
        self.assertFalse(self.presenter.have_active_stacks)

    def test_get_stack_history(self):
        mock_stack = mock.Mock()
        mock_stack.presenter.images.metadata = metadata = {"metadata": 2}
        stack_id = "stack-id"
        self.presenter.stack_visualisers = {stack_id: mock_stack}
        self.assertIs(self.presenter.get_stack_visualiser_history(stack_id), metadata)

    def test_get_all_stack_visualisers_with_180deg_proj(self):
        mock_stacks = [mock.Mock() for _ in range(3)]

        mock_stacks[0].presenter.images.has_proj180deg.return_value = mock_stacks[
            1].presenter.images.has_proj180deg.return_value = True
        mock_stacks[1].presenter.images.has_proj180deg.return_value = False

        self.presenter.stack_visualisers = {uuid.uuid4(): stack for stack in mock_stacks}

        self.assertListEqual([mock_stacks[0], mock_stacks[2]],
                             self.presenter.get_all_stack_visualisers_with_180deg_proj())

    def test_delete_single_image_stack(self):
        id_to_remove = "id-to-remove"
        self.model.remove_container = mock.Mock(return_value=[id_to_remove])

        self.presenter.stack_visualisers[id_to_remove] = mock_stack = mock.Mock()
        self.presenter.remove_item_from_tree_view = mock.Mock()
        self.presenter._delete_container(id_to_remove)

        self.assertNotIn(id_to_remove, self.presenter.stack_visualisers.keys())
        self.assertNotIn(mock_stack, self.presenter.stack_visualisers.values())

        mock_stack.image_view.close.assert_called_once()
        mock_stack.presenter.delete_data.assert_called_once()
        mock_stack.deleteLater.assert_called_once()

        self.presenter.remove_item_from_tree_view.assert_called_once_with(id_to_remove)
        self.view.model_changed.emit.assert_called_once()

    def test_delete_dataset_and_member_image_stacks(self):
        dataset_id = "dataset-id"
        n_dataset_images = 3
        ids_to_remove = [f"id-{i}" for i in range(3)]
        mock_stacks = [mock.Mock() for _ in range(3)]

        self.model.remove_container = mock.Mock(return_value=ids_to_remove)

        for i in range(n_dataset_images):
            self.presenter.stack_visualisers[ids_to_remove[i]] = mock_stacks[i]

        self.presenter.remove_item_from_tree_view = mock.Mock()
        self.presenter._delete_container(dataset_id)

        for i in range(n_dataset_images):
            self.assertNotIn(ids_to_remove[i], self.presenter.stack_visualisers.keys())
            self.assertNotIn(mock_stacks[i], self.presenter.stack_visualisers.values())
            mock_stacks[i].image_view.close.assert_called_once()
            mock_stacks[i].presenter.delete_data.assert_called_once()
            mock_stacks[i].deleteLater.assert_called_once()

        self.presenter.remove_item_from_tree_view.assert_called_once_with(dataset_id)
        self.view.model_changed.emit.assert_called_once()

    def test_delete_fails_then_presenter_does_nothing(self):
        self.model.remove_container = mock.Mock(return_value=None)
        self.presenter._delete_container("bad-id")
        self.view.model_changed.emit.assert_not_called()

    def test_focus_tab_with_id_not_found(self):
        self.model.image_ids = []
        self.model.datasets = []

        with self.assertRaises(Exception):
            self.presenter._focus_tab(stack_id="not-in-the-stacks-dict")

    def test_focus_tab_with_id_in_dataset(self):
        stack_id = "stack-id"
        self.model.image_ids = [stack_id]
        self.model.datasets = [stack_id]
        self.presenter.stack_visualisers = dict()
        self.presenter.stack_visualisers["other-id"] = mock_stack_tab = mock.Mock()
        self.presenter.notify(Notification.FOCUS_TAB, stack_id=stack_id)

        mock_stack_tab.setVisible.assert_not_called()
        mock_stack_tab.raise_.assert_not_called()

    def test_add_recon(self):
        recon = generate_images()
        stack_id = "stack-id"
        self.presenter.notify(Notification.ADD_RECON, recon_data=recon, stack_id=stack_id)
        self.model.add_recon_to_dataset.assert_called_once_with(recon, stack_id)

    def test_dataset_list(self):
        dataset_1 = Dataset(generate_images())
        dataset_1.name = "dataset-1"
        dataset_2 = Dataset(generate_images())
        dataset_2.name = "dataset-2"
        stack_dataset = StackDataset([generate_images()])

        self.model.datasets = {"id1": dataset_1, "id2": dataset_2, "id3": stack_dataset}

        dataset_list = self.presenter.dataset_list
        assert len(dataset_list) == 2

    def test_add_child_item_to_tree_view_success(self):
        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        top_level_item_mock = self.view.dataset_tree_widget.topLevelItem.return_value
        top_level_item_mock.id = dataset_id = "dataset-id"

        child_id = "child-id"
        child_name = "180"
        self.presenter.add_child_item_to_tree_view(dataset_id, child_id, child_name)
        self.view.create_child_tree_item.assert_called_once_with(top_level_item_mock, child_id, child_name)

    def test_add_child_item_to_tree_view_failure(self):
        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        top_level_item_mock = self.view.dataset_tree_widget.topLevelItem.return_value
        top_level_item_mock.id = "different-id"

        with self.assertRaises(RuntimeError):
            self.presenter.add_child_item_to_tree_view("nonexistent-id", "child-id", "180")


if __name__ == '__main__':
    unittest.main()

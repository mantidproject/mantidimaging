# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
import uuid
from typing import List

from unittest import mock
from unittest.mock import patch, call

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset, MixedDataset
from mantidimaging.core.utility.data_containers import ProjectionAngles
from mantidimaging.gui.dialogs.async_task import TaskWorkerThread
from mantidimaging.gui.windows.image_load_dialog import ImageLoadDialog
from mantidimaging.gui.windows.main import MainWindowView, MainWindowPresenter
from mantidimaging.gui.windows.main.presenter import Notification, RECON_TEXT
from mantidimaging.test_helpers.unit_test_helper import generate_images


def generate_images_with_filenames(n_images: int) -> List[ImageStack]:
    images = []
    for _ in range(n_images):
        im = generate_images()
        im.filenames = ["filename"] * im.data.shape[0]
        images.append(im)
    return images


class MainWindowPresenterTest(unittest.TestCase):
    def setUp(self):
        self.view = mock.create_autospec(MainWindowView)
        self.view.image_load_dialog = mock.create_autospec(ImageLoadDialog)
        self.presenter = MainWindowPresenter(self.view)
        self.images = [generate_images() for _ in range(5)]
        self.dataset = StrictDataset(sample=self.images[0],
                                     flat_before=self.images[1],
                                     flat_after=self.images[2],
                                     dark_before=self.images[3],
                                     dark_after=self.images[4])
        self.presenter.model = self.model = mock.Mock()
        self.model.get_recons_id = mock.Mock()

        self.view.create_stack_window.return_value = dock_mock = mock.Mock()
        self.view.model_changed = mock.Mock()
        self.view.dataset_tree_widget = mock.Mock()
        self.view.get_dataset_tree_view_item = mock.Mock()

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

    def create_stack_mocks(self, dataset):
        stack_mocks = []
        for images_id in dataset.all_image_ids:
            stack_mock = mock.Mock()
            stack_mock.id = images_id
            stack_mocks.append(stack_mock)
        self.view.create_stack_window.side_effect = stack_mocks

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
        self.view.image_load_dialog.get_parameters.return_value = parameters_mock

        self.presenter.load_image_files()

        start_async_mock.assert_called_once_with(self.view, self.presenter.model.do_load_dataset,
                                                 self.presenter._on_dataset_load_done, {'parameters': parameters_mock})

    @mock.patch("mantidimaging.gui.windows.main.presenter.start_async_task_view")
    def test_load_stack(self, start_async_mock: mock.Mock):
        file_path = mock.Mock()

        self.presenter.load_image_stack(file_path)

        start_async_mock.assert_called_once_with(self.view, self.presenter.model.load_images_into_mixed_dataset,
                                                 self.presenter._on_stack_load_done, {'file_path': file_path})

    def test_add_stack(self):
        images = generate_images()
        dock_mock = mock.Mock()
        sample_dock_mock = mock.Mock()
        stack_visualiser_mock = mock.Mock()

        dock_mock.widget.return_value = stack_visualiser_mock
        self.view.create_stack_window.return_value = dock_mock

        self.presenter._create_and_tabify_stack_window(images, sample_dock_mock)

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

        self.presenter._create_and_tabify_stack_window(images, sample_dock_mock)
        self.presenter._create_and_tabify_stack_window(images2, sample_dock_mock)

        self.assertEqual(2, self.view.create_stack_window.call_count)
        self.view.tabifyDockWidget.assert_called_with(sample_dock_mock, dock_mock)
        self.assertEqual(2, self.view.tabifyDockWidget.call_count)

    def test_create_new_stack_images(self):
        self.view.model_changed.emit = mock.Mock()
        images = generate_images()
        self.presenter._create_lone_stack_window(images)
        self.assertEqual(1, len(self.presenter.stack_visualisers))

    @mock.patch("mantidimaging.gui.windows.main.presenter.QApplication")
    def test_create_new_stack_images_focuses_newest_tab(self, mock_QApp):
        pass

    def test_create_new_stack_with_180_in_sample(self):
        self.dataset.proj180deg = generate_images(shape=(1, 20, 20))
        self.dataset.proj180deg.filenames = ["filename"]

        self.dataset.flat_before.filenames = ["filename"] * 10
        self.dataset.dark_before.filenames = ["filename"] * 10
        self.dataset.flat_after.filenames = ["filename"] * 10
        self.dataset.dark_after.filenames = ["filename"] * 10

        self.create_stack_mocks(self.dataset)

        self.presenter.create_strict_dataset_stack_windows(self.dataset)

        self.assertEqual(6, len(self.presenter.stack_visualisers))

    @mock.patch("mantidimaging.gui.windows.main.presenter.MainWindowPresenter.add_child_item_to_tree_view")
    @mock.patch("mantidimaging.gui.windows.main.presenter.MainWindowPresenter.get_stack_visualiser")
    def test_create_new_stack_dataset_and_use_threshold_180(self, mock_get_stack, mock_add_child):
        self.dataset.sample.set_projection_angles(
            ProjectionAngles(np.linspace(0, np.pi, self.dataset.sample.num_images)))

        self.dataset.flat_before.filenames = ["filename"] * 10
        self.dataset.dark_before.filenames = ["filename"] * 10
        self.dataset.flat_after.filenames = ["filename"] * 10
        self.dataset.dark_after.filenames = ["filename"] * 10

        self.view.ask_to_use_closest_to_180.return_value = False

        self.dataset.sample.clear_proj180deg()
        self.presenter.add_alternative_180_if_required(self.dataset)

    def test_threshold_180_is_separate_data(self):
        self.dataset.sample.set_projection_angles(
            ProjectionAngles(np.linspace(0, np.pi, self.dataset.sample.num_images)))

        self.presenter.get_stack_visualiser = mock.Mock()
        self.presenter._create_and_tabify_stack_window = mock.Mock()
        self.dataset.sample.clear_proj180deg()
        self.presenter.add_alternative_180_if_required(self.dataset)

        self.assertIsNone(self.dataset.proj180deg.data.base)

    def test_create_new_stack_dataset_and_reject_180(self):
        self.dataset.flat_before.filenames = ["filename"] * 10
        self.dataset.dark_before.filenames = ["filename"] * 10
        self.dataset.flat_after.filenames = ["filename"] * 10
        self.dataset.dark_after.filenames = ["filename"] * 10

        self.view.ask_to_use_closest_to_180.return_value = False

        self.dataset.sample.clear_proj180deg()
        self.presenter.add_alternative_180_if_required(self.dataset)
        self.assertIsNone(self.dataset.proj180deg)

    def test_wizard_action_load(self):
        self.presenter.wizard_action_load()
        self.view.show_image_load_dialog.assert_called_once()

    def test_wizard_action_show_operation(self):
        OPERATION_STR = "ROI Normalisation"
        self.presenter.show_operation(OPERATION_STR)
        self.view.show_filters_window.assert_called_once()
        self.view.filters.presenter.set_filter_by_name.assert_called_once_with(OPERATION_STR)

    def test_wizard_action_show_reconstruction(self):
        self.presenter.wizard_action_show_reconstruction()
        self.view.show_recon_window.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.main.presenter.MainWindowPresenter.add_alternative_180_if_required")
    def test_nexus_load_success_calls_show_information(self, _):
        self.view.nexus_load_dialog = mock.Mock()
        data_title = "data tile"
        self.view.nexus_load_dialog.presenter.get_dataset.return_value = self.dataset, data_title
        self.presenter.create_strict_dataset_stack_windows = mock.Mock()
        self.presenter.load_nexus_file()
        self.presenter.create_strict_dataset_stack_windows.assert_called_once_with(self.dataset)

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

    def test_add_log_to_sample(self):
        self.presenter.add_log_to_sample("doesn't exist", "log file")
        self.presenter.model.add_log_to_sample.assrt_called_with("doesn't exist", "log file")

    def test_do_rename_stack(self):
        self.presenter.stack_visualisers["stack-id"] = mock_stack = mock.Mock()
        mock_stack.windowTitle.return_value = previous_title = "previous title"
        new_title = "new title"
        self.presenter._do_rename_stack(previous_title, new_title)
        mock_stack.setWindowTitle.assert_called_once_with(new_title)
        self.view.model_changed.emit.assert_called_once()

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

    def test_add_first_180_deg_to_dataset(self):
        dataset_id = "dataset-id"
        filename_for_180 = "path/to/180"
        self.model.get_existing_180_id.return_value = None
        self.model.add_180_deg_to_dataset.return_value = _180_deg = generate_images((1, 200, 200))
        self.presenter.add_child_item_to_tree_view = mock.Mock()

        self.presenter.add_180_deg_file_to_dataset(dataset_id, filename_for_180)
        self.model.add_180_deg_to_dataset.assert_called_once_with(dataset_id, filename_for_180)
        self.presenter.add_child_item_to_tree_view.assert_called_once_with(dataset_id, _180_deg.id, "180")
        self.view.model_changed.emit.assert_called_once()

    def test_replace_180_deg_in_dataset(self):
        dataset_id = "dataset-id"
        filename_for_180 = "path/to/180"
        self.model.get_existing_180_id.return_value = existing_180_id = "prev-id"
        self.presenter.stack_visualisers[existing_180_id] = existing_180_stack = mock.Mock()
        self.model.add_180_deg_to_dataset.return_value = _180_deg = generate_images((1, 200, 200))
        self.presenter.replace_child_item_id = mock.Mock()

        self.presenter.add_180_deg_file_to_dataset(dataset_id, filename_for_180)
        self.model.add_180_deg_to_dataset.assert_called_once_with(dataset_id, filename_for_180)
        self.presenter.replace_child_item_id.assert_called_once_with(dataset_id, existing_180_id, _180_deg.id)
        self.assertNotIn(existing_180_stack, self.presenter.stack_visualisers)
        self.view.model_changed.emit.assert_called_once()

    def test_replace_child_item_id_success(self):
        dataset_tree_item_mock = self.view.get_dataset_tree_view_item.return_value
        dataset_tree_item_mock.childCount.return_value = 1
        child_item_mock = dataset_tree_item_mock.child.return_value
        child_item_mock.id = id_to_replace = "id-to-replace"

        dataset_id = "dataset-id"
        new_id = "new-id"

        self.presenter.replace_child_item_id(dataset_id, id_to_replace, new_id)
        self.view.get_dataset_tree_view_item.assert_called_once_with(dataset_id)
        dataset_tree_item_mock.childCount.assert_called_once()
        dataset_tree_item_mock.child.assert_called_once_with(0)
        assert child_item_mock._id == new_id

    def test_replace_child_item_id_failure(self):
        dataset_tree_item_mock = self.view.get_dataset_tree_view_item.return_value
        dataset_tree_item_mock.childCount.return_value = 1

        with self.assertRaises(RuntimeError):
            self.presenter.replace_child_item_id("dataset-id", "bad-id", "new-id")

    def test_add_projection_angles_to_stack(self):
        id, angles = "doesn't-exist", ProjectionAngles(np.ndarray([1]))
        self.presenter.add_projection_angles_to_sample(id, angles)
        self.model.add_projection_angles_to_sample.assert_called_with(id, angles)

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

    def test_delete_single_image_stack(self):
        id_to_remove = "id-to-remove"
        self.model.remove_container = mock.Mock(return_value=[id_to_remove])

        self.presenter.stack_visualisers[id_to_remove] = mock_stack = mock.Mock()
        self.presenter.remove_item_from_tree_view = mock.Mock()
        self.presenter._delete_container(id_to_remove)

        self._check_stack_visualiser_removed(id_to_remove, mock_stack)
        self.presenter.remove_item_from_tree_view.assert_called_once_with(id_to_remove)
        self.view.model_changed.emit.assert_called_once()

    def test_delete_sample_stack_with_180(self):
        ids_to_remove = ["sample-to-remove", "proj_180_to_remove"]
        self.model.remove_container = mock.Mock(return_value=ids_to_remove)
        self.presenter.stack_visualisers[ids_to_remove[0]] = mock_sample = mock.Mock()
        self.presenter.stack_visualisers[ids_to_remove[1]] = mock_180 = mock.Mock()
        self.presenter.remove_item_from_tree_view = mock.Mock()

        self.presenter._delete_container(ids_to_remove[0])

        self._check_stack_visualiser_removed(ids_to_remove[0], mock_sample)
        self._check_stack_visualiser_removed(ids_to_remove[1], mock_180)

        calls = [call(ids_to_remove[0]), call(ids_to_remove[1])]
        self.presenter.remove_item_from_tree_view.assert_has_calls(calls, any_order=True)
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

    def test_focus_tab_with_id_not_found(self):
        self.model.image_ids = []
        self.model.datasets = []
        self.model.recon_list_ids = []

        with self.assertRaises(RuntimeError):
            self.presenter._restore_and_focus_tab(stack_id="not-in-the-stacks-dict")

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
        parent_id = "parent-id"
        self.model.add_recon_to_dataset.return_value = parent_id
        self.presenter.add_recon_item_to_tree_view = mock.Mock()

        self.presenter.notify(Notification.ADD_RECON, recon_data=recon, stack_id=stack_id)
        self.model.add_recon_to_dataset.assert_called_once_with(recon, stack_id)
        self.presenter.add_recon_item_to_tree_view.assert_called_with(parent_id, recon.id, recon.name)
        self.view.create_new_stack.assert_called_once_with(recon)
        self.view.model_changed.emit.assert_called_once()

    def test_dataset_list(self):
        dataset_1 = StrictDataset(generate_images())
        dataset_1.name = "dataset-1"
        dataset_2 = StrictDataset(generate_images())
        dataset_2.name = "dataset-2"
        mixed_dataset = MixedDataset([generate_images()])

        self.model.datasets = {"id1": dataset_1, "id2": dataset_2, "id3": mixed_dataset}

        dataset_list = self.presenter.strict_dataset_list
        assert len(dataset_list) == 2

    def test_add_child_item_to_tree_view(self):
        dataset_item_mock = self.view.get_dataset_tree_view_item.return_value
        dataset_item_mock.id = dataset_id = "dataset-id"

        child_id = "child-id"
        child_name = "180"
        self.presenter.add_child_item_to_tree_view(dataset_id, child_id, child_name)
        self.view.create_child_tree_item.assert_called_once_with(dataset_item_mock, child_id, child_name)

    @mock.patch("mantidimaging.gui.windows.main.presenter.MainWindowPresenter.create_mixed_dataset_tree_view_items")
    def test_on_stack_load_done_success(self, _):
        task = mock.Mock()
        task.result = result_mock = mock.Mock()
        task.was_successful.return_value = True
        task.kwargs = {'file_path': "a/stack/path"}
        self.presenter.create_mixed_dataset_stack_windows = mock.Mock()

        self.presenter._on_stack_load_done(task)
        self.presenter.create_mixed_dataset_stack_windows.assert_called_once_with(result_mock)
        self.view.model_changed.emit.assert_called_once()

    def test_on_dataset_load_done_success(self):
        task = mock.Mock()
        task.result = result_mock = mock.Mock()
        task.was_successful.return_value = True
        self.presenter._add_strict_dataset_to_view = mock.Mock()

        self.presenter._on_dataset_load_done(task)
        self.presenter._add_strict_dataset_to_view.assert_called_once_with(result_mock)
        self.view.model_changed.emit.assert_called_once()

    @patch("mantidimaging.gui.windows.main.presenter.find_projection_closest_to_180")
    def test_no_need_for_alternative_180(self, find_180_mock: mock.Mock):
        dataset = StrictDataset(generate_images())
        dataset.proj180deg = generate_images((1, 20, 20))
        dataset.proj180deg.filenames = ["filename"]

        self.presenter.add_alternative_180_if_required(dataset)
        find_180_mock.assert_not_called()

    def test_create_mixed_dataset_stack_windows(self):
        n_stacks = 3
        dataset = MixedDataset([generate_images() for _ in range(n_stacks)], "cool-name")
        self.create_stack_mocks(dataset)
        self.presenter.create_mixed_dataset_stack_windows(dataset)
        assert len(self.presenter.stack_visualisers) == n_stacks

    def test_tabify_stack_window_to_sample_stack(self):
        new_stack = mock.Mock()
        sample_stack = mock.Mock()
        self.presenter.stack_visualisers = {"new-id": new_stack, "sample-id": sample_stack}
        self.presenter._tabify_stack_window(new_stack, sample_stack)
        self.view.tabifyDockWidget.assert_called_once_with(sample_stack, new_stack)

    def test_tabify_stack_window_to_item_in_list(self):
        new_stack = mock.Mock()
        other_stack = mock.Mock()
        self.presenter.stack_visualisers = {"new-id": new_stack, "other-id": other_stack}
        self.presenter._tabify_stack_window(new_stack)
        self.view.tabifyDockWidget.assert_called_once_with(other_stack, new_stack)

    def test_create_strict_dataset_tree_view_items(self):
        dataset = StrictDataset(*generate_images_with_filenames(5))
        dataset.proj180deg = generate_images((1, 20, 20))
        dataset.proj180deg.filenames = ["filename"]

        dataset_tree_item_mock = self.view.create_dataset_tree_widget_item.return_value
        self.presenter.create_strict_dataset_tree_view_items(dataset)

        s_call = call(dataset_tree_item_mock, dataset.sample.id, "Projections")
        fb_call = call(dataset_tree_item_mock, dataset.flat_before.id, "Flat Before")
        fa_call = call(dataset_tree_item_mock, dataset.flat_after.id, "Flat After")
        db_call = call(dataset_tree_item_mock, dataset.dark_before.id, "Dark Before")
        da_call = call(dataset_tree_item_mock, dataset.dark_after.id, "Dark After")
        _180_call = call(dataset_tree_item_mock, dataset.proj180deg.id, "180")

        self.view.create_child_tree_item.assert_has_calls([s_call, fb_call, fa_call, db_call, da_call, _180_call])
        self.view.add_item_to_tree_view.assert_called_once_with(dataset_tree_item_mock)

    def test_add_recon_item_to_tree_view_first_item(self):
        dataset_item_mock = self.view.get_dataset_tree_view_item.return_value
        dataset_item_mock.id = parent_id = "parent-id"
        child_id = "child-id"
        name = "Recon"
        recon_group_mock = self.view.add_recon_group.return_value
        self.model.get_recon_list_id.return_value = recons_id = "recons-id"
        self.view.get_recon_group.return_value = None

        self.presenter.add_recon_item_to_tree_view(parent_id, child_id, name)
        self.view.get_dataset_tree_view_item.assert_called_once_with(parent_id)
        self.model.get_recon_list_id.assert_called_once_with(parent_id)
        self.view.add_recon_group.assert_called_once_with(dataset_item_mock, recons_id)
        self.view.create_child_tree_item.assert_called_once_with(recon_group_mock, child_id, name)

    def test_add_recon_item_to_tree_view_additional_item(self):
        parent_id = "parent-id"
        dataset_item_mock = self.view.get_dataset_tree_view_item.return_value
        child_id = "child-id"
        recon_group_mock = self.view.get_recon_group.return_value
        name = "Recon_2"

        self.presenter.add_recon_item_to_tree_view(parent_id, child_id, name)
        self.view.get_dataset_tree_view_item.assert_called_once_with(parent_id)
        self.view.get_recon_group.assert_called_once_with(dataset_item_mock)
        self.view.create_child_tree_item.assert_called_once_with(recon_group_mock, child_id, name)

    def test_add_recon_item_to_tree_view_first_item_with_multiple_recons(self):
        child_id = "child-id"
        name = "Recon"
        recon_group_mock = self.view.add_recon_group.return_value
        self.view.get_recon_group.return_value = None

        self.presenter.add_recon_item_to_tree_view("parent-id", child_id, name)

        self.view.add_recon_group.assert_called_once()
        self.view.create_child_tree_item.assert_called_once_with(recon_group_mock, child_id, name)

    def test_created_mixed_dataset_tree_view_items(self):
        n_images = 3
        dataset = MixedDataset([generate_images() for _ in range(n_images)])
        dataset.name = dataset_name = "mixed-dataset"
        dataset_tree_item_mock = self.view.create_dataset_tree_widget_item.return_value

        calls = []
        for i in range(n_images):
            dataset.all[i].name = f"name-{i}"
            calls.append(call(dataset_tree_item_mock, dataset.all[i].id, dataset.all[i].name))

        self.presenter.create_mixed_dataset_tree_view_items(dataset)

        self.view.create_dataset_tree_widget_item.assert_called_once_with(dataset_name, dataset.id)
        self.view.create_child_tree_item.assert_has_calls(calls)
        self.view.add_item_to_tree_view.assert_called_once_with(dataset_tree_item_mock)

    def test_cant_focus_on_recon_group(self):
        self.presenter.stack_visualisers = dict()
        self.model.datasets = []
        self.presenter.stack_visualisers["stack-id"] = stack_mock = mock.Mock()
        recons_id = "recons-id"
        self.model.recon_list_ids = [recons_id]

        self.presenter._restore_and_focus_tab(recons_id)
        stack_mock.setVisible.assert_not_called()
        stack_mock._raise.assert_not_called()

    def test_add_sinograms_to_dataset_with_no_sinograms_and_update_view(self):
        sinograms = generate_images()
        ds = StrictDataset(generate_images())
        self.model.datasets = dict()
        self.model.datasets[ds.id] = ds
        self.model.get_parent_dataset.return_value = ds.id

        dataset_item_mock = self.view.get_dataset_tree_view_item.return_value
        dataset_item_mock.id = ds.id
        self.view.get_sinograms_item.return_value = None
        self.presenter.create_single_tabbed_images_stack = mock.Mock()
        self.presenter._delete_stack = mock.Mock()

        self.presenter.add_sinograms_to_dataset_and_update_view(sinograms, ds.sample.id)
        self.model.get_parent_dataset.assert_called_once_with(ds.sample.id)
        self.presenter._delete_stack.assert_not_called()
        self.assertIs(ds.sinograms, sinograms)
        self.view.get_dataset_tree_view_item.assert_called_once_with(ds.id)
        self.view.get_sinograms_item.assert_called_once_with(dataset_item_mock)
        self.view.create_child_tree_item.assert_called_once_with(dataset_item_mock, sinograms.id, self.view.sino_text)
        self.presenter.create_single_tabbed_images_stack.assert_called_once_with(sinograms)
        self.view.model_changed.emit.assert_called_once()

    def test_add_sinograms_to_dataset_with_existing_sinograms_and_update_view(self):
        new_sinograms = generate_images()
        ds = StrictDataset(generate_images())
        self.model.datasets = dict()
        self.model.datasets[ds.id] = ds
        self.model.get_parent_dataset.return_value = ds.id
        ds.sinograms = existing_sinograms = generate_images()

        dataset_item_mock = self.view.get_dataset_tree_view_item.return_value
        dataset_item_mock.id = ds.id
        sinograms_item_mock = self.view.get_sinograms_item.return_value
        self.presenter.create_single_tabbed_images_stack = mock.Mock()
        self.presenter._delete_stack = mock.Mock()

        self.presenter.add_sinograms_to_dataset_and_update_view(new_sinograms, ds.sample.id)
        self.presenter._delete_stack.assert_called_once_with(existing_sinograms.id)
        self.assertIs(ds.sinograms, new_sinograms)
        self.view.get_dataset_tree_view_item.assert_called_once_with(ds.id)
        self.view.get_sinograms_item.assert_called_once_with(dataset_item_mock)
        assert sinograms_item_mock._id == new_sinograms.id
        self.presenter.create_single_tabbed_images_stack.assert_called_once_with(new_sinograms)
        self.view.model_changed.emit.assert_called_once()

    def test_remove_item_from_recon_group_but_keep_group(self):
        top_level_item_mock = mock.Mock()
        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        self.view.dataset_tree_widget.topLevelItem.return_value = top_level_item_mock
        top_level_item_mock.childCount.return_value = 1
        top_level_item_mock.child.return_value = recon_group_mock = mock.Mock()

        recon_group_mock.childCount.side_effect = [2, 2, 1]
        recon_to_delete = mock.Mock()
        recon_to_delete.id = recon_to_delete_id = "recon-to-delete-id"
        recon_group_mock.child.side_effect = [mock.Mock(), recon_to_delete]

        self.presenter.remove_item_from_tree_view(recon_to_delete_id)
        recon_group_mock.takeChild.assert_called_once_with(1)
        top_level_item_mock.takeChild.assert_not_called()

    def test_remove_item_from_recon_group_and_remove_group(self):
        top_level_item_mock = mock.Mock()
        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        self.view.dataset_tree_widget.topLevelItem.return_value = top_level_item_mock
        top_level_item_mock.childCount.return_value = 1
        top_level_item_mock.child.return_value = recon_group_mock = mock.Mock()

        recon_group_mock.childCount.side_effect = [1, 1, 0]
        recon_group_mock.child.return_value = recon_to_delete = mock.Mock()
        recon_to_delete.id = recon_to_delete_id = "recon-to-delete-id"

        self.presenter.remove_item_from_tree_view(recon_to_delete_id)
        recon_group_mock.takeChild.assert_called_once_with(0)
        top_level_item_mock.takeChild.assert_called_once_with(0)

    def test_nothing_removed_from_recon_group(self):
        top_level_item_mock = mock.Mock()
        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        self.view.dataset_tree_widget.topLevelItem.return_value = top_level_item_mock
        top_level_item_mock.childCount.return_value = 2
        recon_group_mock = mock.Mock()
        other_data_mock = mock.Mock()
        other_data_mock.id = item_to_delete_id = "item-to-delete-id"
        top_level_item_mock.child.side_effect = [recon_group_mock, other_data_mock]

        recon_group_mock.childCount.return_value = 1
        recon_group_mock.child.return_value = mock.Mock()

        self.presenter.remove_item_from_tree_view(item_to_delete_id)
        recon_group_mock.takeChild.assert_not_called()
        top_level_item_mock.takeChild.assert_called_once_with(1)

    def test_save_nexus_fails_when_no_nexus_save_dialog(self):
        self.presenter.view.nexus_save_dialog = None
        with self.assertRaises(AssertionError):
            self.presenter.save_nexus_file()

    @mock.patch("mantidimaging.gui.windows.main.presenter.start_async_task_view")
    def test_save_nexus_file(self, start_async_mock: mock.Mock):
        self.view.nexus_save_dialog = nexus_save_dialog_mock = mock.Mock()
        nexus_save_dialog_mock.save_path.return_value = save_path = "nexus/save/path"
        nexus_save_dialog_mock.sample_name.return_value = sample_name = "sample-name"
        nexus_save_dialog_mock.selected_dataset = dataset_id = "dataset-id"

        self.presenter.notify(Notification.NEXUS_SAVE)
        start_async_mock.assert_called_once_with(self.presenter.view,
                                                 self.model.do_nexus_saving,
                                                 self.presenter._on_save_done, {
                                                     'dataset_id': dataset_id,
                                                     'path': save_path,
                                                     'sample_name': sample_name
                                                 },
                                                 busy=True)

    def test_get_dataset(self):
        test_ds = StrictDataset(generate_images())
        other_ds = StrictDataset(generate_images())
        self.model.datasets = dict()
        self.model.datasets[test_ds.id] = test_ds
        self.model.datasets[other_ds.id] = other_ds

        result = self.presenter.get_dataset(test_ds.id)
        self.assertEqual(result, test_ds)

    def test_get_dataset_not_found(self):
        ds = StrictDataset(generate_images())
        incorrect_id = uuid.uuid4()
        self.model.datasets = dict()
        self.model.datasets[ds.id] = ds

        result = self.presenter.get_dataset(incorrect_id)
        self.assertIsNone(result)

    def _check_stack_visualiser_removed(self, stack_id, mock_stack_visualiser):
        self.assertNotIn(stack_id, self.presenter.stack_visualisers.keys())
        self.assertNotIn(mock_stack_visualiser, self.presenter.stack_visualisers.values())

        mock_stack_visualiser.image_view.close.assert_called_once()
        mock_stack_visualiser.presenter.delete_data.assert_called_once()
        mock_stack_visualiser.deleteLater.assert_called_once()

    def test_show_add_stack_to_dataset_dialog_called_with_dataset_id(self):
        dataset_id = "dataset-id"
        self.model.datasets.keys.return_value = [dataset_id]
        self.presenter.notify(Notification.SHOW_ADD_STACK_DIALOG, container_id=dataset_id)
        self.view.show_add_stack_to_existing_dataset_dialog.assert_called_once_with(dataset_id)

    def test_show_add_stack_to_dataset_dialog_called_with_stack_id(self):
        dataset_id = "dataset-id"
        self.model.datasets.keys.return_value = []
        self.model.get_parent_dataset.return_value = dataset_id
        self.presenter.notify(Notification.SHOW_ADD_STACK_DIALOG, container_id="stack-id")
        self.view.show_add_stack_to_existing_dataset_dialog.assert_called_once_with(dataset_id)

    def test_add_new_stack_to_strict_dataset(self):
        self.model.datasets = dict()
        self.dataset.flat_before = None
        self.model.datasets[self.dataset.id] = self.dataset

        self.view.add_to_dataset_dialog = mock.Mock()
        self.view.add_to_dataset_dialog.dataset_id = self.dataset.id
        self.view.add_to_dataset_dialog.presenter.images = new_images = generate_images()
        self.view.add_to_dataset_dialog.images_type = images_type = "Flat Before"

        self.presenter.add_child_item_to_tree_view = mock.Mock()
        self.presenter.create_single_tabbed_images_stack = mock.Mock()

        self.presenter._add_images_to_existing_dataset()
        self.presenter.add_child_item_to_tree_view.assert_called_once_with(self.dataset.id, new_images.id, images_type)
        self.presenter.create_single_tabbed_images_stack.assert_called_once_with(new_images)
        self.view.model_changed.emit.assert_called_once()
        self.assertIs(self.dataset.flat_before, new_images)

    def test_replace_existing_stack_in_strict_dataset(self):
        self.model.datasets = dict()
        self.model.datasets[self.dataset.id] = self.dataset
        prev_images_id = self.dataset.flat_before.id

        self.view.add_to_dataset_dialog = mock.Mock()
        self.view.add_to_dataset_dialog.dataset_id = self.dataset.id
        self.view.add_to_dataset_dialog.presenter.images = new_images = generate_images()
        self.view.add_to_dataset_dialog.images_type = "Flat Before"

        self.presenter.create_single_tabbed_images_stack = mock.Mock()
        self.presenter.replace_child_item_id = mock.Mock()
        self.presenter._delete_stack = mock.Mock()

        self.presenter.notify(Notification.DATASET_ADD)
        self.presenter.replace_child_item_id.assert_called_once_with(self.dataset.id, prev_images_id, new_images.id)
        self.presenter._delete_stack.assert_called_once_with(prev_images_id)
        self.presenter.create_single_tabbed_images_stack.assert_called_once_with(new_images)
        self.view.model_changed.emit.assert_called_once()
        self.assertIs(self.dataset.flat_before, new_images)

    def test_add_stack_to_mixed_dataset(self):
        self.model.datasets = dict()
        mixed_dataset = MixedDataset()
        self.model.datasets[mixed_dataset.id] = mixed_dataset

        self.view.add_to_dataset_dialog = mock.Mock()
        self.view.add_to_dataset_dialog.dataset_id = mixed_dataset.id
        self.view.add_to_dataset_dialog.presenter.images = new_images = generate_images()
        self.presenter.add_child_item_to_tree_view = mock.Mock()

        self.presenter._add_images_to_existing_dataset()
        self.assertIn(new_images, mixed_dataset.all)
        self.presenter.add_child_item_to_tree_view.assert_called_once_with(mixed_dataset.id, new_images.id,
                                                                           new_images.name)

    def test_add_recon_to_mixed_dataset(self):
        mixed_dataset = MixedDataset([generate_images()])
        recon = generate_images()
        recon.name = "recon-name"

        self.view.add_to_dataset_dialog.images_type = RECON_TEXT
        self.presenter.add_recon_item_to_tree_view = mock.Mock()
        self.presenter.get_dataset = mock.Mock(return_value=mixed_dataset)
        self.view.add_to_dataset_dialog.presenter.images = recon

        self.presenter._add_images_to_existing_dataset()

        self.assertIn(recon, mixed_dataset.recons.stacks)
        self.presenter.add_recon_item_to_tree_view.assert_called_once_with(mixed_dataset.id, recon.id, recon.name)

    def test_add_recon_to_strict_dataset(self):
        self.presenter.add_recon_item_to_tree_view = mock.Mock()
        self.view.add_to_dataset_dialog.images_type = RECON_TEXT

        recon = generate_images()
        recon.name = "recon-name"
        self.presenter.add_recon_item_to_tree_view = mock.Mock()
        self.presenter.get_dataset = mock.Mock(return_value=self.dataset)
        self.view.add_to_dataset_dialog.presenter.images = recon

        self.presenter._add_images_to_existing_dataset()

        self.assertIn(recon, self.dataset.recons.stacks)
        self.presenter.add_recon_item_to_tree_view.assert_called_once_with(self.dataset.id, recon.id, recon.name)

    def test_select_tree_widget_item(self):
        tree_widget_item = mock.Mock()
        self.presenter._select_tree_widget_item(tree_widget_item)
        tree_widget_item.setSelected.assert_called_once_with(True)
        self.view.dataset_tree_widget.clearSelection.assert_called_once()

    def test_select_top_level_item(self):
        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        self.view.dataset_tree_widget.topLevelItem.return_value = mock_top_level_item = mock.Mock()
        mock_top_level_item.id = mock_id = "id"

        self.presenter._set_tree_view_selection_with_id(mock_id)
        self.view.dataset_tree_widget.clearSelection.assert_called_once()
        mock_top_level_item.setSelected.assert_called_once_with(True)

    def test_select_stack_item(self):
        mock_stack_widget = mock.Mock()
        mock_stack_widget.id = mock_id = "stack-id"

        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        self.view.dataset_tree_widget.topLevelItem.return_value = mock_top_level_item = mock.Mock()
        mock_top_level_item.id = "dataset-id"

        mock_top_level_item.childCount.return_value = 1
        mock_stack_item = mock_top_level_item.child.return_value
        mock_stack_item.id = mock_id

        self.presenter.notify(Notification.TAB_CLICKED, stack=mock_stack_widget)

        self.view.dataset_tree_widget.clearSelection.assert_called_once()
        mock_stack_item.setSelected.assert_called_once_with(True)

    def test_select_recon_item(self):
        mock_recon_widget = mock.Mock()
        mock_recon_widget.id = mock_id = "recon-id"

        self.view.dataset_tree_widget.topLevelItemCount.return_value = 1
        self.view.dataset_tree_widget.topLevelItem.return_value = mock_top_level_item = mock.Mock()
        mock_top_level_item.id = "dataset-id"

        mock_top_level_item.childCount.return_value = 1
        mock_recon_group = mock_top_level_item.child.return_value
        mock_recon_group.childCount.return_value = 1
        mock_recon_group.id = "recon-group-id"
        mock_recon_item = mock_recon_group.child.return_value
        mock_recon_item.id = mock_id

        self.presenter.notify(Notification.TAB_CLICKED, stack=mock_recon_widget)

        self.view.dataset_tree_widget.clearSelection.assert_called_once()
        mock_recon_item.setSelected.assert_called_once_with(True)

    def test_all_stack_ids(self):
        self.model.datasets = dict()

        mixed_stacks = [generate_images() for _ in range(5)]
        mixed_dataset = MixedDataset(mixed_stacks)

        strict_stacks = [generate_images() for _ in range(5)]
        strict_dataset = StrictDataset(*strict_stacks)

        all_ids = [stack.id for stack in mixed_stacks] + [stack.id for stack in strict_stacks]
        self.model.datasets[mixed_dataset.id] = mixed_dataset
        self.model.datasets[strict_dataset.id] = strict_dataset

        self.assertListEqual(all_ids, self.presenter.all_stack_ids)


if __name__ == '__main__':
    unittest.main()

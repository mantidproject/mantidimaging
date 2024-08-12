# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import DEFAULT, Mock
from uuid import uuid4

from unittest import mock
import numpy as np
from PyQt5.QtWidgets import QDialog

from mantidimaging.core.data.dataset import StrictDataset, MixedDataset, Dataset
from mantidimaging.core.utility.data_containers import ProjectionAngles
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.main.presenter import Notification as PresNotification, Notification
from mantidimaging.gui.windows.main.view import RECON_GROUP_TEXT, SINO_TEXT
from mantidimaging.test_helpers import start_qapplication, mock_versions
from mantidimaging.test_helpers.unit_test_helper import generate_images


@mock_versions
@start_qapplication
class MainWindowViewTest(unittest.TestCase):

    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            with mock.patch("mantidimaging.gui.windows.main.view.CommandLineArguments") as command_line_args:
                command_line_args.return_value.path.return_value = ""
                command_line_args.return_value.operation.return_value = ""
                command_line_args.return_value.recon.return_value = False
                command_line_args.return_value.live_viewer.return_value = ""
                command_line_args.return_value.spectrum_viewer.return_value = False

                self.view = MainWindowView()
        self.presenter = mock.MagicMock()
        self.view.presenter = self.presenter
        self.view.dataset_tree_widget = self.dataset_tree_widget = mock.Mock()

    def test_execute_save(self):
        self.view.execute_image_file_save()

        self.presenter.notify.assert_called_once_with(PresNotification.IMAGE_FILE_SAVE)

    @mock.patch("mantidimaging.gui.windows.main.view.DatasetSelectorDialog")
    @mock.patch("mantidimaging.gui.windows.main.view.QFileDialog.getOpenFileName")
    def test_load_180_deg_dialog(self, get_open_file_name: mock.Mock, dataset_selector_dialog: mock.Mock):
        dataset_selector_dialog.return_value.exec.return_value = QDialog.DialogCode.Accepted
        dataset_id = "dataset-id"
        dataset_selector_dialog.return_value.selected_id = dataset_id
        selected_file = "~/home/test/directory/selected_file.tif"
        get_open_file_name.return_value = (selected_file, None)
        _180_dataset = mock.MagicMock()
        self.presenter.add_180_deg_file_to_dataset.return_value = _180_dataset

        self.view.load_180_deg_dialog()

        dataset_selector_dialog.assert_called_once_with(main_window=self.view,
                                                        title='Dataset Selector',
                                                        message="Which dataset is the 180 projection being loaded for?")
        get_open_file_name.assert_called_once_with(caption="180 Degree Image",
                                                   filter="Image File (*.tif *.tiff);;All (*.*)",
                                                   initialFilter="Image File (*.tif *.tiff)")
        self.presenter.add_180_deg_file_to_dataset.assert_called_once_with(dataset_id=dataset_id,
                                                                           _180_deg_file=selected_file)

    def test_execute_load(self):
        self.view.execute_image_file_load()

        self.presenter.notify.assert_called_once_with(PresNotification.IMAGE_FILE_LOAD)

    def test_execute_nexus_load(self):
        self.view.execute_nexus_load()
        self.presenter.notify.assert_called_once_with(PresNotification.NEXUS_LOAD)

    @mock.patch("mantidimaging.gui.windows.main.view.ImageLoadDialog")
    def test_show_load_dialog(self, mock_load: mock.Mock):
        self.view.show_image_load_dialog()

        mock_load.assert_called_once_with(self.view)
        mock_load.return_value.show.assert_called_once_with()

    @mock.patch("mantidimaging.gui.windows.main.view.WizardPresenter")
    def test_show_wizard(self, mock_wizard: mock.Mock):
        self.view.show_wizard()

        mock_wizard.assert_called_once_with(self.view)
        mock_wizard.return_value.show.assert_called_once_with()

    @mock.patch("mantidimaging.gui.windows.main.view.ReconstructWindowView")
    def test_show_recon_window(self, mock_recon: mock.Mock):
        self.view.show_recon_window()

        mock_recon.assert_called_once_with(self.view)
        mock_recon.return_value.show.assert_called_once_with()
        mock_recon.return_value.activateWindow.assert_not_called()
        mock_recon.return_value.raise_.assert_not_called()

        self.view.show_recon_window()
        mock_recon.assert_called_once_with(self.view)
        mock_recon.return_value.activateWindow.assert_called_once_with()
        mock_recon.return_value.raise_.assert_called_once_with()

    @mock.patch("mantidimaging.gui.windows.main.view.FiltersWindowView")
    def test_show_filters_window(self, mock_filters: mock.Mock):
        self.view.show_filters_window()

        mock_filters.assert_called_once_with(self.view)
        mock_filters.return_value.show.assert_called_once_with()
        mock_filters.return_value.activateWindow.assert_not_called()
        mock_filters.return_value.raise_.assert_not_called()

        self.view.show_filters_window()
        mock_filters.assert_called_once_with(self.view)
        mock_filters.return_value.activateWindow.assert_called_once_with()
        mock_filters.return_value.raise_.assert_called_once_with()

    def test_create_new_stack(self):
        images = generate_images()
        self.view.create_new_stack(images)

        self.presenter.create_single_tabbed_images_stack.assert_called_once_with(images)

    def test_rename_stack(self):
        self.view.rename_stack("apples", "oranges")

        self.presenter.notify.assert_called_once_with(PresNotification.RENAME_STACK,
                                                      current_name="apples",
                                                      new_name="oranges")

    @mock.patch("mantidimaging.gui.windows.main.view.getLogger")
    @mock.patch("mantidimaging.gui.windows.main.view.MainWindowView.show_error_dialog")
    def test_uncaught_exception(self, mock_show_error_dialog, mock_getlogger):
        self.view.uncaught_exception("user-error", "log-error")

        mock_show_error_dialog.assert_called_once()
        self.assertIn("user-error", mock_show_error_dialog.call_args[0][0])
        mock_getlogger.return_value.error.assert_called_once_with("log-error")

    @mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter")
    def test_show_about(self, mock_welcomescreen: mock.Mock):
        self.view.show_about()
        mock_welcomescreen.assert_called_once_with(self.view)

    @mock.patch("mantidimaging.gui.windows.main.view.QDesktopServices")
    def test_open_online_documentation(self, mock_qtdeskserv: mock.Mock):
        self.view.open_online_documentation()
        mock_qtdeskserv.openUrl.assert_called_once()

    @mock.patch.multiple("mantidimaging.gui.windows.main.view.MainWindowView",
                         setCentralWidget=DEFAULT,
                         addDockWidget=DEFAULT)
    @mock.patch("mantidimaging.gui.windows.main.view.StackVisualiserView")
    def test_create_stack_window(self, mock_sv: mock.Mock, setCentralWidget: mock.Mock, addDockWidget: mock.Mock):
        images = generate_images()
        position = "test_position"
        floating = False

        self.view.splitter = splitter_mock = mock.Mock()

        self.view.create_stack_window(images, position=position, floating=floating)

        mock_sv.assert_called_once_with(self.view, images)
        dock = mock_sv.return_value
        setCentralWidget.assert_called_once_with(splitter_mock)
        addDockWidget.assert_called_once_with(position, dock)

        splitter_mock.addWidget.assert_called_once_with(mock_sv.return_value)

        dock.setFloating.assert_called_once_with(floating)

    @mock.patch("mantidimaging.gui.windows.main.view.QMessageBox")
    @mock.patch("mantidimaging.gui.windows.main.view.ProjectionAngleFileParser")
    @mock.patch("mantidimaging.gui.windows.main.view.DatasetSelectorDialog")
    @mock.patch("mantidimaging.gui.windows.main.view.QFileDialog.getOpenFileName")
    def test_load_projection_angles(self, getOpenFileName: mock.Mock, DatasetSelectorDialog: mock.Mock,
                                    ProjectionAngleFileParser: Mock, QMessageBox: Mock):
        DatasetSelectorDialog.return_value.exec.return_value = QDialog.DialogCode.Accepted
        selected_stack = "selected_id"
        DatasetSelectorDialog.return_value.selected_id = selected_stack

        selected_file = "~/home/test/directory/selected_file.txt"
        getOpenFileName.return_value = (selected_file, None)

        proj_angles = ProjectionAngles(np.arange(0, 10))
        ProjectionAngleFileParser.return_value.get_projection_angles.return_value = proj_angles

        self.view.load_projection_angles()

        DatasetSelectorDialog.assert_called_once_with(main_window=self.view,
                                                      title='Stack Selector',
                                                      message=self.view.LOAD_PROJECTION_ANGLES_DIALOG_MESSAGE,
                                                      show_stacks=True)
        getOpenFileName.assert_called_once_with(caption=self.view.LOAD_PROJECTION_ANGLES_FILE_DIALOG_CAPTION,
                                                filter="All (*.*)",
                                                initialFilter="All (*.*)")

        self.presenter.add_projection_angles_to_sample.assert_called_once_with(selected_stack, proj_angles)
        QMessageBox.information.assert_called_once()

    def test_update_shortcuts_with_presenter_with_one_or_more_stacks(self):
        self.presenter.datasets = [Dataset()]

        self._update_shortcuts_test(False, True)
        self._update_shortcuts_test(True, True)

    def test_update_shortcuts_with_presenter_with_no_stacks(self):
        self.presenter.datasets = []

        self._update_shortcuts_test(False, False)
        self._update_shortcuts_test(True, False)

    def _update_shortcuts_test(self, original_state, has_stacks):
        self.view.actionSaveImages.setEnabled(original_state)
        self.view.actionSampleLoadLog.setEnabled(original_state)
        self.view.actionLoad180deg.setEnabled(original_state)
        self.view.actionLoadProjectionAngles.setEnabled(original_state)
        self.view.menuWorkflow.setEnabled(original_state)
        self.view.menuImage.setEnabled(original_state)

        self.view.update_shortcuts()

        self.assertEqual(has_stacks, self.view.actionSaveImages.isEnabled())
        self.assertEqual(has_stacks, self.view.actionSampleLoadLog.isEnabled())
        self.assertEqual(has_stacks, self.view.actionLoad180deg.isEnabled())
        self.assertEqual(has_stacks, self.view.actionLoadProjectionAngles.isEnabled())
        self.assertEqual(has_stacks, self.view.menuWorkflow.isEnabled())
        self.assertEqual(has_stacks, self.view.menuImage.isEnabled())

    @mock.patch("mantidimaging.gui.windows.main.view.populate_menu")
    def test_populate_image_menu_with_no_stack(self, populate_menu):
        self.view.menuImage = mock.MagicMock()
        self.view.current_showing_stack = mock.MagicMock(return_value=None)

        self.view.populate_image_menu()

        populate_menu.assert_not_called()
        self.view.menuImage.addAction.assert_called_once_with("No stack loaded!")

    @mock.patch("mantidimaging.gui.windows.main.view.populate_menu")
    def test_populate_image_menu_with_stack_and_actions(self, populate_menu):
        self.view.menuImage = mock.MagicMock()
        stack = mock.MagicMock()
        actions = mock.MagicMock()
        stack.actions = actions
        self.view.current_showing_stack = mock.MagicMock(return_value=stack)

        self.view.populate_image_menu()

        populate_menu.assert_called_once_with(self.view.menuImage, actions)
        self.view.menuImage.addAction.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.main.view.StackVisualiserView")
    def test_current_showing_stack_with_stack_with_visible(self, stack_visualiser_view):
        stack = mock.MagicMock()
        stack.visibleRegion.return_value.isEmpty.return_value = False
        self.view.findChildren = mock.MagicMock(return_value=[stack])

        current_stack = self.view.current_showing_stack()

        self.assertEqual(stack, current_stack)
        stack.visibleRegion.assert_called_once()
        stack.visibleRegion.return_value.isEmpty.assert_called_once()
        self.view.findChildren.assert_called_once_with(stack_visualiser_view)

    @mock.patch("mantidimaging.gui.windows.main.view.StackVisualiserView")
    def test_current_showing_stack_with_stack_not_visible(self, stack_visualiser_view):
        stack = mock.MagicMock()
        stack.visibleRegion.return_value.isEmpty.return_value = True
        self.view.findChildren = mock.MagicMock(return_value=[stack])

        current_stack = self.view.current_showing_stack()

        self.assertEqual(None, current_stack)
        stack.visibleRegion.assert_called_once()
        stack.visibleRegion.return_value.isEmpty.assert_called_once()
        self.view.findChildren.assert_called_once_with(stack_visualiser_view)

    @mock.patch("mantidimaging.gui.windows.main.view.StackVisualiserView")
    def test_current_showing_stack_no_stack(self, stack_visualiser_view):
        stack = mock.MagicMock()
        self.view.findChildren = mock.MagicMock(return_value=[])

        current_stack = self.view.current_showing_stack()

        self.assertEqual(None, current_stack)
        stack.visibleRegion.assert_not_called()
        stack.visibleRegion.return_value.isEmpty.assert_not_called()
        self.view.findChildren.assert_called_once_with(stack_visualiser_view)

    def test_get_images_from_stack_uuid(self):
        uuid = uuid4()
        images = mock.MagicMock()
        self.presenter.get_stack_visualiser.return_value.presenter.images = images

        return_value = self.view.get_images_from_stack_uuid(uuid)

        self.presenter.get_stack_visualiser.assert_called_once_with(uuid)
        self.assertEqual(images, return_value)

    def test_load_image_stack(self):
        selected_file = "file_name"
        self.view._get_file_name = mock.MagicMock(return_value=selected_file)

        self.view.load_image_stack()

        self.presenter.load_image_stack.assert_called_once_with(selected_file)
        self.view._get_file_name.assert_called_once_with("Image", "Image File (*.tif *.tiff)")

    def test_show_nexus_load_dialog_calls_show(self):
        self.view._get_file_name = mock.MagicMock()
        with mock.patch("mantidimaging.gui.windows.main.view.NexusLoadDialog") as nexus_load_dialog:
            self.view.show_nexus_load_dialog()
        nexus_load_dialog.assert_called_once()
        nexus_load_dialog.return_value.show.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.main.view.CommandLineArguments")
    @mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter")
    @mock.patch("mantidimaging.gui.windows.main.view.MainWindowPresenter")
    def test_load_path_from_command_line(self, main_window_presenter, welcome_screen_presenter, command_line_args):
        test_path = "./"
        command_line_args.return_value.path.return_value = [test_path]
        command_line_args.return_value.recon.return_value = False
        command_line_args.return_value.operation.return_value = ""
        command_line_args.return_value.live_viewer.return_value = ""
        command_line_args.return_value.spectrum_viewer.return_value = False
        MainWindowView()
        main_window_presenter.return_value.load_stacks_from_folder.assert_called_once_with(test_path)

    @mock.patch("mantidimaging.gui.windows.main.view.CommandLineArguments")
    @mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter")
    @mock.patch("mantidimaging.gui.windows.main.view.MainWindowPresenter")
    def test_command_line_no_path_argument_set(self, main_window_presenter, welcome_screen_presenter,
                                               command_line_args):
        command_line_args.return_value.path.return_value = ""
        command_line_args.return_value.recon.return_value = False
        command_line_args.return_value.operation.return_value = ""
        command_line_args.return_value.live_viewer.return_value = ""
        command_line_args.return_value.spectrum_viewer.return_value = False
        MainWindowView()
        main_window_presenter.return_value.load_stacks_from_folder.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.main.view.CommandLineArguments")
    @mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter")
    @mock.patch("mantidimaging.gui.windows.main.view.FiltersWindowView")
    def test_command_line_dont_show_filters_window(self, filters_window, welcome_screen_presenter, command_line_args):
        command_line_args.return_value.path.return_value = ""
        command_line_args.return_value.recon.return_value = False
        command_line_args.return_value.operation.return_value = ""
        command_line_args.return_value.live_viewer.return_value = ""
        command_line_args.return_value.spectrum_viewer.return_value = False
        MainWindowView()
        filters_window.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.main.view.CommandLineArguments")
    @mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter")
    @mock.patch("mantidimaging.gui.windows.main.view.ReconstructWindowView")
    def test_command_line_dont_show_recon_window(self, recon_window, welcome_screen_presenter, command_line_args):
        command_line_args.return_value.path.return_value = ""
        command_line_args.return_value.recon.return_value = False
        command_line_args.return_value.operation.return_value = ""
        command_line_args.return_value.live_viewer.return_value = ""
        command_line_args.return_value.spectrum_viewer.return_value = False
        MainWindowView()
        recon_window.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.main.view.QTreeDatasetWidgetItem")
    def test_add_recon_group(self, dataset_widget_item_mock):
        dataset_item_mock = mock.Mock()
        recons_id = "recon-id"

        recon_group_mock = self.view.add_recon_group(dataset_item_mock, recons_id)
        dataset_widget_item_mock.assert_called_once_with(dataset_item_mock, recons_id)
        recon_group_mock.setText.assert_called_once_with(0, RECON_GROUP_TEXT)
        dataset_item_mock.addChild.assert_called_once_with(recon_group_mock)

    def test_get_recon_group_success(self):
        dataset_item_mock = mock.Mock()
        dataset_item_mock.childCount.return_value = n_children = 3
        item_mocks = [mock.Mock() for _ in range(n_children)]
        dataset_item_mock.child.side_effect = lambda i: item_mocks[i]
        item_mocks[0].text.return_value = "Projections"
        item_mocks[1].text.return_value = "Flat Before"
        item_mocks[2].text.return_value = RECON_GROUP_TEXT
        recon_item_mock = item_mocks[2]

        returned_item = self.view.get_recon_group(dataset_item_mock)
        assert returned_item is recon_item_mock

    def test_get_recon_group_failure(self):
        dataset_item_mock = mock.Mock()
        dataset_item_mock.childCount.return_value = n_children = 3
        item_mocks = [mock.Mock() for _ in range(n_children)]
        dataset_item_mock.child.side_effect = lambda i: item_mocks[i]
        item_mocks[0].text.return_value = "Projections"
        item_mocks[1].text.return_value = "Flat Before"
        item_mocks[2].text.return_value = "Flat After"

        self.assertIsNone(self.view.get_recon_group(dataset_item_mock))

    def test_get_all_180_projections(self):
        self.assertIs(self.view.get_all_180_projections(), self.presenter.get_all_180_projections.return_value)

    def test_get_sinograms_item(self):
        n_children = 3
        children = [mock.Mock() for _ in range(n_children)]
        children[0].text.return_value = children[1].text.return_value = "Not Sinograms"
        children[2].text.return_value = SINO_TEXT

        parent_mock = mock.Mock()
        parent_mock.childCount.return_value = n_children
        parent_mock.child.side_effect = children

        self.assertIs(self.view.get_sinograms_item(parent_mock), children[2])

    def test_get_sinograms_item_returns_none(self):
        n_children = 3
        children = [mock.Mock() for _ in range(n_children)]
        children[0].text.return_value = children[1].text.return_value = children[2].text.return_value = "Not Sinograms"

        parent_mock = mock.Mock()
        parent_mock.childCount.return_value = n_children
        parent_mock.child.side_effect = children

        self.assertIsNone(self.view.get_sinograms_item(parent_mock))

    def test_get_dataset_tree_view_item_success(self):
        self.dataset_tree_widget.topLevelItemCount.return_value = 1
        dataset_tree_view_item_mock = self.dataset_tree_widget.topLevelItem.return_value
        dataset_tree_view_item_mock.id = dataset_id = "dataset-id"
        self.assertIs(dataset_tree_view_item_mock, self.view.get_dataset_tree_view_item(dataset_id))

    def test_get_dataset_tree_view_item_failure(self):
        self.dataset_tree_widget.topLevelItemCount.return_value = 1
        with self.assertRaises(RuntimeError):
            self.view.get_dataset_tree_view_item("bad-dataset-id")

    def test_execute_nexus_save(self):
        self.view.execute_nexus_save()
        self.presenter.notify.assert_called_once_with(PresNotification.NEXUS_SAVE)

    @mock.patch("mantidimaging.gui.windows.main.view.ImageSaveDialog")
    def test_show_image_save_dialog(self, image_save_dialog_mock):
        self.view.show_image_save_dialog()
        image_save_dialog_mock.assert_called_once_with(self.view, self.view.stack_list)
        image_save_dialog_mock.return_value.show.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.main.view.NexusSaveDialog")
    def test_show_nexus_save_dialog(self, nexus_save_dialog_mock):
        self.view.show_nexus_save_dialog()
        nexus_save_dialog_mock.assert_called_once_with(self.view, self.view.strict_dataset_list)
        nexus_save_dialog_mock.return_value.show.assert_called_once()

    def test_execute_add_to_dataset_calls_notify(self):
        self.view.execute_add_to_dataset()
        self.presenter.notify.assert_called_once_with(Notification.DATASET_ADD)

    def test_add_images_to_existing_dataset_sends_container_id(self):
        mock_dataset = mock.Mock()
        mock_dataset.id = dataset_id = "dataset-id"
        self.dataset_tree_widget.selectedItems.return_value = [mock_dataset]
        self.presenter.all_dataset_ids = [dataset_id]

        self.view._add_images_to_existing_dataset()
        self.presenter.notify.assert_called_once_with(PresNotification.SHOW_ADD_STACK_DIALOG, container_id=dataset_id)

    def test_show_add_stack_to_existing_dataset_dialog_with_strict_dataset(self):
        mock_strict_dataset = mock.Mock(spec=StrictDataset)
        mock_strict_dataset.id = strict_dataset_id = "strict-dataset-id"
        mock_strict_dataset.name = strict_dataset_name = "strict-dataset-name"
        self.presenter.get_dataset.return_value = mock_strict_dataset

        with mock.patch("mantidimaging.gui.windows.main.view.AddImagesToDatasetDialog") as add_images_mock:
            self.view.show_add_stack_to_existing_dataset_dialog(strict_dataset_id)

        add_images_mock.assert_called_once_with(self.view, strict_dataset_id, True, strict_dataset_name)

    def test_show_add_stack_to_existing_dataset_dialog_with_mixed_dataset(self):
        mock_mixed_dataset = mock.Mock(spec=MixedDataset)
        mock_mixed_dataset.name = mixed_dataset_name = "mixed-dataset-name"
        mixed_dataset_id = "mixed-dataset-id"
        self.presenter.get_dataset.return_value = mock_mixed_dataset

        with mock.patch("mantidimaging.gui.windows.main.view.AddImagesToDatasetDialog") as add_images_mock:
            self.view.show_add_stack_to_existing_dataset_dialog(mixed_dataset_id)

        add_images_mock.assert_called_once_with(self.view, mixed_dataset_id, False, mixed_dataset_name)

    def test_tab_bar_clicked(self):
        mock_stack = mock.Mock()
        self.view._on_tab_bar_clicked(mock_stack)
        self.presenter.notify.assert_called_once_with(Notification.TAB_CLICKED, stack=mock_stack)

    def test_execute_move_stack(self):
        origin_dataset_id = "origin-dataset-id"
        stack_id = "stack-id"
        destination_stack_type = "Flat Before"
        destination_dataset_id = "destination-dataset-id"

        self.view.execute_move_stack(origin_dataset_id, stack_id, destination_stack_type, destination_dataset_id)
        self.presenter.notify.assert_called_once_with(PresNotification.MOVE_STACK,
                                                      origin_dataset_id=origin_dataset_id,
                                                      stack_id=stack_id,
                                                      destination_stack_type=destination_stack_type,
                                                      destination_dataset_id=destination_dataset_id)

    def test_move_stack(self):
        stack_to_move = mock.Mock()
        stack_to_move.id = stack_to_move_id = "stack-to-move-id"
        self.view.dataset_tree_widget.selectedItems = mock.Mock(return_value=[stack_to_move])

        self.view._move_stack()
        self.presenter.notify.assert_called_once_with(PresNotification.SHOW_MOVE_STACK_DIALOG,
                                                      stack_id=stack_to_move_id)

    def test_show_move_stack_dialog(self):
        origin_dataset_id = "origin-dataset-id"
        stack_id = "stack-id"
        origin_dataset_name = "origin-dataset-name"
        stack_data_type = "Dark After"

        with mock.patch("mantidimaging.gui.windows.main.view.MoveStackDialog") as move_stack_mock:
            self.view.show_move_stack_dialog(origin_dataset_id, stack_id, origin_dataset_name, stack_data_type)
            move_stack_mock.assert_called_once_with(self.view, origin_dataset_id, stack_id, origin_dataset_name,
                                                    stack_data_type)
            move_stack_mock.return_value.show.assert_called_once()

    def test_is_dataset_strict(self):
        ds_id = "ds-id"
        self.view.is_dataset_strict(ds_id)
        self.presenter.is_dataset_strict.assert_called_once_with(ds_id)

    @mock.patch("PyQt5.QtWidgets.QFileDialog.getExistingDirectory")
    @mock.patch("mantidimaging.gui.windows.main.MainWindowView.show_live_viewer")
    def test_live_viewer_asks_for_data_dir(self, mock_show_live_viewer, mock_get_existing_dir):
        mock_path = Path("/test/path")
        mock_get_existing_dir.return_value = str(mock_path)

        self.view.live_view_choose_directory()

        mock_show_live_viewer.assert_called_once_with(mock_path)

    @mock.patch("PyQt5.QtWidgets.QFileDialog.getExistingDirectory")
    @mock.patch("mantidimaging.gui.windows.main.MainWindowView.show_live_viewer")
    def test_live_viewer_asks_for_data_dir_no_path(self, mock_show_live_viewer, mock_get_existing_dir):
        mock_get_existing_dir.return_value = ""

        self.view.live_view_choose_directory()

        mock_show_live_viewer.assert_not_called()

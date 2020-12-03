# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import numpy as np
from mantidimaging.core.utility.data_containers import ProjectionAngles
import unittest
import mock

from PyQt5.QtWidgets import QDialog
from mock import DEFAULT, Mock

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.main.presenter import Notification as PresNotification
from mantidimaging.test_helpers import start_qapplication
from mantidimaging.test_helpers.unit_test_helper import generate_images


@start_qapplication
class MainWindowViewTest(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.check_version_and_label") as check_version_and_label:
            self.view = MainWindowView()
            self.presenter = mock.MagicMock()
            self.view.presenter = self.presenter
            self.check_version_and_label = check_version_and_label

    def test_execute_save(self):
        self.view.execute_save()

        self.presenter.notify.assert_called_once_with(PresNotification.SAVE)

    def test_find_images_stack_title(self):
        images = mock.MagicMock()
        self.presenter.get_stack_with_images = mock.MagicMock()

        return_value = self.view.find_images_stack_title(images)

        self.presenter.get_stack_with_images.assert_called_once_with(images)
        self.assertEqual(return_value, self.presenter.get_stack_with_images.return_value.name)

    @mock.patch("mantidimaging.gui.windows.main.view.StackSelectorDialog")
    @mock.patch("mantidimaging.gui.windows.main.view.Qt.QFileDialog.getOpenFileName")
    def test_load_180_deg_dialog(self, get_open_file_name: mock.Mock, stack_selector_dialog: mock.Mock):
        stack_selector_dialog.return_value.exec.return_value = QDialog.Accepted
        selected_stack = "selected_stack"
        stack_selector_dialog.return_value.selected_stack = selected_stack
        selected_file = "~/home/test/directory/selected_file.tif"
        get_open_file_name.return_value = (selected_file, None)
        _180_dataset = mock.MagicMock()
        self.presenter.add_180_deg_to_sample.return_value = _180_dataset
        self.view.create_new_stack = mock.MagicMock()  # type: ignore
        selected_filename = "selected_file.tif"
        self.presenter.create_stack_name = mock.MagicMock(return_value=selected_filename)

        self.view.load_180_deg_dialog()

        stack_selector_dialog.assert_called_once_with(main_window=self.view,
                                                      title='Stack Selector',
                                                      message='Which stack is the 180 degree projection being loaded '
                                                      'for?')
        get_open_file_name.assert_called_once_with(caption="180 Degree Image",
                                                   filter="Image File (*.tif *.tiff);;All (*.*)",
                                                   initialFilter="Image File (*.tif *.tiff)")
        self.presenter.add_180_deg_to_sample.assert_called_once_with(stack_name=selected_stack,
                                                                     _180_deg_file=selected_file)
        self.presenter.create_stack_name.assert_called_once_with(selected_file)
        self.view.create_new_stack.assert_called_once_with(_180_dataset, selected_filename)

    def test_execute_load(self):
        self.view.execute_load()

        self.presenter.notify.assert_called_once_with(PresNotification.LOAD)

    @mock.patch("mantidimaging.gui.windows.main.view.MWLoadDialog")
    def test_show_load_dialogue(self, mock_load: mock.Mock):
        self.view.show_load_dialogue()

        mock_load.assert_called_once_with(self.view)
        mock_load.return_value.show.assert_called_once_with()

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
        self.view.create_new_stack(images, "Test Title")

        self.presenter.create_new_stack.assert_called_once_with(images, "Test Title")

    def test_update_stack_with_images(self):
        images = generate_images()
        self.view.update_stack_with_images(images)

        self.presenter.update_stack_with_images.assert_called_once_with(images)

    def test_remove_stack(self):
        fake_stack_vis = mock.Mock()
        fake_stack_vis.uuid = "test-uuid"
        self.view.remove_stack(fake_stack_vis)

        self.presenter.notify.assert_called_once_with(PresNotification.REMOVE_STACK, uuid="test-uuid")

    def test_rename_stack(self):
        self.view.rename_stack("apples", "oranges")

        self.presenter.notify.assert_called_once_with(PresNotification.RENAME_STACK,
                                                      current_name="apples",
                                                      new_name="oranges")

    @mock.patch("mantidimaging.gui.windows.main.view.QtWidgets")
    def test_not_latest_version_warning(self, mock_qtwidgets):
        self.view.not_latest_version_warning("test-message")

        mock_qtwidgets.QMessageBox.warning.assert_called_once_with(self.view, self.view.NOT_THE_LATEST_VERSION,
                                                                   "test-message")

    @mock.patch("mantidimaging.gui.windows.main.view.getLogger")
    @mock.patch("mantidimaging.gui.windows.main.view.QtWidgets")
    def test_uncaught_exception(self, mock_qtwidgets, mock_getlogger):
        self.view.uncaught_exception("user-error", "log-error")

        mock_qtwidgets.QMessageBox.critical.assert_called_once_with(self.view, self.view.UNCAUGHT_EXCEPTION,
                                                                    "user-error")
        mock_getlogger.return_value.error.assert_called_once_with("log-error")

    @mock.patch("mantidimaging.gui.windows.main.view.QtWidgets")
    def test_show_about(self, mock_qtwidgets: mock.Mock):
        self.view.show_about()

        mock_qtwidgets.QMessageBox.assert_called_once()
        mock_qtwidgets.QMessageBox.return_value.setWindowTitle.assert_called_once()
        mock_qtwidgets.QMessageBox.return_value.setTextFormat.assert_called_once()
        mock_qtwidgets.QMessageBox.return_value.setText.assert_called_once()
        mock_qtwidgets.QMessageBox.return_value.show.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.main.view.QtGui")
    def test_open_online_documentation(self, mock_qtgui: mock.Mock):
        self.view.open_online_documentation()
        mock_qtgui.QDesktopServices.openUrl.assert_called_once()

    @mock.patch.multiple("mantidimaging.gui.windows.main.view.MainWindowView",
                         setCentralWidget=DEFAULT,
                         addDockWidget=DEFAULT)
    @mock.patch("mantidimaging.gui.windows.main.view.StackVisualiserView")
    @mock.patch("mantidimaging.gui.windows.main.view.Qt")
    def test_create_stack_window(self,
                                 mock_qt: mock.Mock,
                                 mock_sv: mock.Mock,
                                 setCentralWidget: Mock = Mock(),
                                 addDockWidget: Mock = Mock()):
        images = generate_images()
        title = "test_title"
        position = "test_position"
        floating = False

        self.view.create_stack_window(images, title, position=position, floating=floating)

        mock_qt.QDockWidget.assert_called_once_with(title, self.view)
        dock = mock_qt.QDockWidget.return_value
        setCentralWidget.assert_called_once_with(dock)
        addDockWidget.assert_called_once_with(position, dock)

        mock_sv.assert_called_once_with(self.view, dock, images)
        dock.setWidget.assert_called_once_with(mock_sv.return_value)
        dock.setFloating.assert_called_once_with(floating)

    @mock.patch("mantidimaging.gui.windows.main.view.QMessageBox")
    @mock.patch("mantidimaging.gui.windows.main.view.ProjectionAngleFileParser")
    @mock.patch("mantidimaging.gui.windows.main.view.StackSelectorDialog")
    @mock.patch("mantidimaging.gui.windows.main.view.Qt.QFileDialog.getOpenFileName")
    def test_load_projection_angles(self, getOpenFileName: mock.Mock, StackSelectorDialog: mock.Mock,
                                    ProjectionAngleFileParser: Mock, QMessageBox: Mock):
        StackSelectorDialog.return_value.exec.return_value = QDialog.Accepted
        selected_stack = "selected_stack"
        StackSelectorDialog.return_value.selected_stack = selected_stack

        selected_file = "~/home/test/directory/selected_file.txt"
        getOpenFileName.return_value = (selected_file, None)

        proj_angles = ProjectionAngles(np.arange(0, 10))
        ProjectionAngleFileParser.return_value.get_projection_angles.return_value = proj_angles

        self.presenter.add_projection_angles_to_sample
        self.view.load_projection_angles()

        StackSelectorDialog.assert_called_once_with(main_window=self.view,
                                                    title='Stack Selector',
                                                    message=self.view.LOAD_PROJECTION_ANGLES_DIALOG_MESSAGE)
        getOpenFileName.assert_called_once_with(caption=self.view.LOAD_PROJECTION_ANGLES_FILE_DIALOG_CAPTION,
                                                filter="All (*.*)")

        self.presenter.add_projection_angles_to_sample.assert_called_once_with(selected_stack, proj_angles)
        QMessageBox.information.assert_called_once()

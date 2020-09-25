# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from PyQt5.QtWidgets import QDialog

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

    @mock.patch("mantidimaging.gui.windows.main.view.StackSelectorDialog")
    @mock.patch("mantidimaging.gui.windows.main.view.Qt.QFileDialog.getOpenFileName")
    def test_load_180_deg_dialog(self, get_open_file_name: mock.Mock, stack_selector_diag: mock.Mock):
        stack_selector_diag.return_value.exec.return_value = QDialog.Accepted
        selected_stack = "selected_stack"
        stack_selector_diag.return_value.selected_stack = selected_stack
        selected_file = "~/home/test/directory/selected_file.tif"
        get_open_file_name.return_value = (selected_file, None)
        _180_dataset = mock.MagicMock()
        self.presenter.add_180_deg_to_sample.return_value = _180_dataset
        self.view.create_new_stack = mock.MagicMock()  # type: ignore
        selected_filename = "selected_file.tif"
        self.presenter.create_stack_name = mock.MagicMock(return_value=selected_filename)

        self.view.load_180_deg_dialog()

        stack_selector_diag.assert_called_once_with(main_window=self.view,
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

    def test_execute_save(self):
        view = MainWindowView()
        view.presenter.notify = mock.Mock()
        view.execute_save()

        view.presenter.notify.assert_called_once_with(PresNotification.SAVE)

    def test_execute_load(self):
        view = MainWindowView()
        view.presenter.notify = mock.Mock()
        view.execute_load()

        view.presenter.notify.assert_called_once_with(PresNotification.LOAD)

    @mock.patch("mantidimaging.gui.windows.main.view.MWLoadDialog")
    def test_show_load_dialogue(self, mock_load: mock.Mock):
        view = MainWindowView()
        view.show_load_dialogue()

        mock_load.assert_called_once_with(view)
        mock_load.return_value.show.assert_called_once_with()

    @mock.patch("mantidimaging.gui.windows.main.view.ReconstructWindowView")
    def test_show_recon_window(self, mock_recon: mock.Mock):
        view = MainWindowView()
        view.show_recon_window()

        mock_recon.assert_called_once_with(view)
        mock_recon.return_value.show.assert_called_once_with()
        mock_recon.return_value.activateWindow.assert_not_called()
        mock_recon.return_value.raise_.assert_not_called()

        view.show_recon_window()
        mock_recon.assert_called_once_with(view)
        mock_recon.return_value.activateWindow.assert_called_once_with()
        mock_recon.return_value.raise_.assert_called_once_with()

    @mock.patch("mantidimaging.gui.windows.main.view.FiltersWindowView")
    def test_show_filters_window(self, mock_filters: mock.Mock):
        view = MainWindowView()
        view.show_filters_window()

        mock_filters.assert_called_once_with(view)
        mock_filters.return_value.show.assert_called_once_with()
        mock_filters.return_value.activateWindow.assert_not_called()
        mock_filters.return_value.raise_.assert_not_called()

        view.show_filters_window()
        mock_filters.assert_called_once_with(view)
        mock_filters.return_value.activateWindow.assert_called_once_with()
        mock_filters.return_value.raise_.assert_called_once_with()

    @mock.patch("mantidimaging.gui.windows.main.view.SavuFiltersWindowView")
    def test_show_savu_filters_window(self, mock_savu_filters: mock.Mock):
        view = MainWindowView()
        view.show_savu_filters_window()

        mock_savu_filters.assert_called_once_with(view)
        mock_savu_filters.return_value.show.assert_called_once_with()
        mock_savu_filters.return_value.activateWindow.assert_not_called()
        mock_savu_filters.return_value.raise_.assert_not_called()

        view.show_savu_filters_window()
        mock_savu_filters.assert_called_once_with(view)
        mock_savu_filters.return_value.activateWindow.assert_called_once_with()
        mock_savu_filters.return_value.raise_.assert_called_once_with()

    @mock.patch("mantidimaging.gui.windows.main.view.QtWidgets")
    @mock.patch("mantidimaging.gui.windows.main.view.SavuFiltersWindowView", side_effect=RuntimeError("Test message"))
    def test_show_savu_filters_window_no_backend(self, mock_savu_filters: mock.Mock, mock_widgets: mock.Mock):
        view = MainWindowView()
        view.show_savu_filters_window()

        mock_savu_filters.assert_called_once_with(view)
        mock_widgets.QMessageBox.warning.assert_called_once_with(view, view.AVAILABLE_MSG, "Test message")

    def test_create_new_stack(self):
        view = MainWindowView()
        view.presenter = mock.Mock()

        images = generate_images()
        view.create_new_stack(images, "Test Title")

        view.presenter.create_new_stack.assert_called_once_with(images, "Test Title")

    def test_update_stack_with_images(self):
        view = MainWindowView()
        view.presenter = mock.Mock()

        images = generate_images()
        view.update_stack_with_images(images)

        view.presenter.update_stack_with_images.assert_called_once_with(images)

    def test_remove_stack(self):
        view = MainWindowView()
        view.presenter = mock.Mock()

        fake_stack_vis = mock.Mock()
        fake_stack_vis.uuid = "test-uuid"
        view.remove_stack(fake_stack_vis)

        view.presenter.notify.assert_called_once_with(PresNotification.REMOVE_STACK, uuid="test-uuid")

    def test_rename_stack(self):
        view = MainWindowView()
        view.presenter.notify = mock.Mock()
        view.rename_stack("apples", "oranges")

        view.presenter.notify.assert_called_once_with(PresNotification.RENAME_STACK,
                                                      current_name="apples",
                                                      new_name="oranges")

    @mock.patch("mantidimaging.gui.windows.main.view.QtWidgets")
    def test_not_latest_version_warning(self, mock_qtwidgets):
        view = MainWindowView()
        view.not_latest_version_warning("test-message")

        mock_qtwidgets.QMessageBox.warning.assert_called_once_with(view, view.NOT_THE_LATEST_VERSION, "test-message")

    @mock.patch("mantidimaging.gui.windows.main.view.getLogger")
    @mock.patch("mantidimaging.gui.windows.main.view.QtWidgets")
    def test_uncaught_exception(self, mock_qtwidgets, mock_getlogger):
        view = MainWindowView()
        view.uncaught_exception("user-error", "log-error")

        mock_qtwidgets.QMessageBox.critical.assert_called_once_with(view, view.UNCAUGHT_EXCEPTION, "user-error")
        mock_getlogger.return_value.error.assert_called_once_with("log-error")

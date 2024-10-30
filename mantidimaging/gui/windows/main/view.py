# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import uuid
from logging import getLogger
from pathlib import Path
import time
from typing import TYPE_CHECKING, Any
from uuid import UUID

import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QPoint
from PyQt5.QtGui import QIcon, QDragEnterEvent, QDropEvent, QDesktopServices
from PyQt5.QtWidgets import QAction, QDialog, QLabel, QMessageBox, QMenu, QFileDialog, QSplitter, \
    QTreeWidgetItem, QTreeWidget

from mantidimaging.core.data import ImageStack
from mantidimaging.core.io.utility import find_first_file_that_is_possibly_a_sample
from mantidimaging.core.utility import finder
from mantidimaging.core.utility.command_line_arguments import CommandLineArguments
from mantidimaging.core.utility.projection_angle_parser import ProjectionAngleFileParser
from mantidimaging.core.utility.version_check import versions
from mantidimaging.gui.dialogs.multiple_stack_select.view import MultipleStackSelect
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility.qt_helpers import populate_menu
from mantidimaging.gui.widgets.dataset_selector_dialog.dataset_selector_dialog import DatasetSelectorDialog
from mantidimaging.gui.windows.add_images_to_dataset_dialog.view import AddImagesToDatasetDialog
from mantidimaging.gui.windows.image_load_dialog import ImageLoadDialog
from mantidimaging.gui.windows.main.nexus_save_dialog import NexusSaveDialog
from mantidimaging.gui.windows.main.presenter import MainWindowPresenter, Notification, StackId
from mantidimaging.gui.windows.main.presenter import Notification as PresNotification
from mantidimaging.gui.windows.main.image_save_dialog import ImageSaveDialog
from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog
from mantidimaging.gui.windows.nexus_load_dialog.view import NexusLoadDialog
from mantidimaging.gui.windows.operations import FiltersWindowView
from mantidimaging.gui.windows.recon import ReconstructWindowView
from mantidimaging.gui.windows.settings.view import SettingsWindowView
from mantidimaging.gui.windows.spectrum_viewer.view import SpectrumViewerWindowView
from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowView
from mantidimaging.gui.windows.stack_choice.compare_presenter import StackComparePresenter
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView
from mantidimaging.gui.windows.welcome_screen.presenter import WelcomeScreenPresenter
from mantidimaging.gui.windows.wizard.presenter import WizardPresenter
from mantidimaging.__main__ import process_start_time

if TYPE_CHECKING:
    from mantidimaging.core.data.dataset import Dataset

RECON_GROUP_TEXT = "Recons"
SINO_TEXT = "Sinograms"

LOG = getLogger(__name__)
perf_logger = getLogger("perf." + __name__)


class QTreeDatasetWidgetItem(QTreeWidgetItem):

    def __init__(self, parent: QTreeWidget, dataset_id: UUID):
        self._id = dataset_id
        super().__init__(parent)

    @property
    def id(self):
        return self._id


class MainWindowView(BaseMainWindowView):
    NOT_THE_LATEST_VERSION = "This is not the latest version"

    # Emitted when a new stack is created or an existing one deleted
    model_changed = pyqtSignal()
    # Emitted when an existing stack is changed
    stack_changed = pyqtSignal()
    backend_message = pyqtSignal(bytes)

    menuFile: QMenu
    menuWorkflow: QMenu
    menuImage: QMenu
    menuHelp: QMenu
    menuTreeView: QMenu | None = None

    actionRecon: QAction
    actionFilters: QAction
    actionCompareImages: QAction
    actionSpectrumViewer: QAction
    actionLiveViewer: QAction
    actionSampleLoadLog: QAction
    actionShutterCounts: QAction
    actionLoadProjectionAngles: QAction
    actionLoad180deg: QAction
    actionLoadDataset: QAction
    actionLoadImages: QAction
    actionLoadNeXusFile: QAction
    actionSaveImages: QAction
    actionSaveNeXusFile: QAction
    actionSettings: QAction
    actionExit: QAction

    filters: FiltersWindowView | None = None
    recon: ReconstructWindowView | None = None
    spectrum_viewer: SpectrumViewerWindowView | None = None
    live_viewer: LiveViewerWindowView | None = None
    settings_window: SettingsWindowView | None = None

    image_load_dialog: ImageLoadDialog | None = None
    image_save_dialog: ImageSaveDialog | None = None
    nexus_load_dialog: NexusLoadDialog | None = None
    nexus_save_dialog: NexusSaveDialog | None = None
    add_to_dataset_dialog: AddImagesToDatasetDialog | None = None
    move_stack_dialog: MoveStackDialog | None = None

    default_theme_enabled: int = 1

    welcome_window: WelcomeScreenPresenter | None = None
    wizard: WizardPresenter | None = None

    def __init__(self, open_dialogs: bool = True):
        super().__init__(None, "gui/ui/main_window.ui")

        self.setWindowTitle("Mantid Imaging")

        self.presenter = MainWindowPresenter(self)

        status_bar = self.statusBar()
        self.status_bar_label = QLabel("", self)
        status_bar.addPermanentWidget(self.status_bar_label)

        self.setup_shortcuts()
        self.update_shortcuts()

        self.setAcceptDrops(True)
        base_path = finder.ROOT_PATH

        self.open_dialogs = open_dialogs
        if self.open_dialogs:
            if versions.is_prerelease():
                self.setWindowTitle("Mantid Imaging Unstable")
                bg_image = os.path.join(base_path, "gui/ui/images/mantid_imaging_unstable_64px.png")
            else:
                bg_image = os.path.join(base_path, "gui/ui/images/mantid_imaging_64px.png")
        else:
            bg_image = os.path.join(base_path, "gui/ui/images/mantid_imaging_64px.png")
        self.setWindowIcon(QIcon(bg_image))

        self.welcome_window = None
        if self.open_dialogs and WelcomeScreenPresenter.show_today():
            self.show_about()

        self.wizard = None

        # Recon and operation windows are launched from view using self.args
        # if passed as flags through cli once data is loaded
        self.args = CommandLineArguments()
        if self.args.path():
            for filepath in list(self.args.path()):
                self.presenter.load_stacks_from_folder(filepath)
        if self.args.live_viewer() != "":
            self.show_live_viewer(live_data_path=Path(self.args.live_viewer()))

        self.dataset_tree_widget = QTreeWidget()
        self.dataset_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dataset_tree_widget.customContextMenuRequested.connect(self._open_tree_menu)
        self.dataset_tree_widget.itemClicked.connect(self._bring_stack_tab_to_front)

        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.addWidget(self.dataset_tree_widget)

        self.dataset_tree_widget.setMinimumWidth(250)
        self.dataset_tree_widget.setMaximumWidth(300)
        self.dataset_tree_widget.setHeaderLabel("")

        self.setCentralWidget(self.splitter)

        self.tabifiedDockWidgetActivated.connect(self._on_tab_bar_clicked)

        self.presenter.do_update_UI()

    def _window_ready(self) -> None:
        if perf_logger.isEnabledFor(1):
            perf_logger.info(f"Mantid Imaging ready in {time.monotonic() - process_start_time}")
        super()._window_ready()

    def setup_shortcuts(self) -> None:
        self.actionLoadDataset.triggered.connect(self.show_image_load_dialog)
        self.actionLoadImages.triggered.connect(self.load_image_stack)
        self.actionLoadNeXusFile.triggered.connect(self.show_nexus_load_dialog)
        self.actionSampleLoadLog.triggered.connect(self.load_sample_log_dialog)
        self.actionShutterCounts.triggered.connect(self.load_shuttercounts_dialog)
        self.actionLoad180deg.triggered.connect(self.load_180_deg_dialog)
        self.actionLoadProjectionAngles.triggered.connect(self.load_projection_angles)
        self.actionSaveImages.triggered.connect(self.show_image_save_dialog)
        self.actionSaveNeXusFile.triggered.connect(self.show_nexus_save_dialog)
        self.actionExit.triggered.connect(self.close)

        self.menuImage.aboutToShow.connect(self.populate_image_menu)

        self.actionOnlineDocumentation.triggered.connect(self.open_online_documentation)
        self.actionAbout.triggered.connect(self.show_about)
        self.actionWizard.triggered.connect(self.show_wizard)

        self.actionFilters.triggered.connect(self.show_filters_window)
        self.actionRecon.triggered.connect(self.show_recon_window)
        self.actionSpectrumViewer.triggered.connect(self.show_spectrum_viewer_window)
        self.actionLiveViewer.triggered.connect(self.live_view_choose_directory)
        self.actionSettings.triggered.connect(self.show_settings_window)

        self.actionCompareImages.triggered.connect(self.show_stack_select_dialog)

        self.model_changed.connect(self.update_shortcuts)

    def populate_image_menu(self) -> None:
        self.menuImage.clear()
        current_stack = self.current_showing_stack()
        if current_stack is None:
            self.menuImage.addAction("No stack loaded!")
        else:
            populate_menu(self.menuImage, current_stack.actions)

    def current_showing_stack(self) -> StackVisualiserView | None:
        for stack in self.findChildren(StackVisualiserView):
            if not stack.visibleRegion().isEmpty():
                return stack
        return None

    def update_shortcuts(self) -> None:
        datasets = list(self.presenter.datasets)
        has_datasets = len(datasets) > 0

        self.actionSaveImages.setEnabled(has_datasets)
        self.actionSaveNeXusFile.setEnabled(has_datasets)
        self.actionSampleLoadLog.setEnabled(has_datasets)
        self.actionShutterCounts.setEnabled(has_datasets)
        self.actionLoad180deg.setEnabled(has_datasets)
        self.actionLoadProjectionAngles.setEnabled(has_datasets)
        self.menuWorkflow.setEnabled(has_datasets)
        self.menuImage.setEnabled(has_datasets)

    @staticmethod
    def open_online_documentation() -> None:
        url = QUrl("https://mantidproject.github.io/mantidimaging/")
        QDesktopServices.openUrl(url)

    def show_about(self) -> None:
        self.welcome_window = WelcomeScreenPresenter(self)
        self.welcome_window.show()

    def show_image_load_dialog(self) -> None:
        self.image_load_dialog = ImageLoadDialog(self)
        self.image_load_dialog.show()

    def show_image_load_dialog_with_path(self, file_path: str) -> bool:
        """
        Open the dataset loading dialog with a given file_path preset as the sample
        """
        sample_file = find_first_file_that_is_possibly_a_sample(file_path)
        if sample_file is None:
            sample_file = find_first_file_that_is_possibly_a_sample(os.path.dirname(file_path))
        if sample_file is not None:
            self.image_load_dialog = ImageLoadDialog(self)
            self.image_load_dialog.presenter.do_update_sample(sample_file)
            self.image_load_dialog.show()
        return sample_file is not None

    def show_nexus_load_dialog(self) -> None:
        self.nexus_load_dialog = NexusLoadDialog(self)
        self.nexus_load_dialog.show()

    def show_wizard(self) -> None:
        if self.wizard is None:
            self.wizard = WizardPresenter(self)
        self.wizard.show()

    @staticmethod
    def _get_file_name(caption: str, file_filter: str = "All (*.*)") -> str:
        if file_filter == "All (*.*)":
            full_filter = file_filter
        else:
            full_filter = f"{file_filter};;All (*.*)"
        selected_file, _ = QFileDialog.getOpenFileName(caption=caption, filter=full_filter, initialFilter=file_filter)
        return selected_file

    def load_image_stack(self) -> None:
        # Open file dialog
        selected_file = self._get_file_name("Image", "Image File (*.tif *.tiff)")

        # Cancel/Close was clicked
        if selected_file == "":
            return

        self.presenter.load_image_stack(selected_file)

    def load_sample_log_dialog(self) -> None:
        stack_selector = DatasetSelectorDialog(main_window=self,
                                               title="Stack Selector",
                                               message="Which stack is the log being loaded for?",
                                               show_stacks=True)
        # Was closed without accepting (e.g. via x button or ESC)
        if QDialog.DialogCode.Accepted != stack_selector.exec():
            return

        stack_to_add_log_to = stack_selector.selected_id

        if stack_to_add_log_to is None:
            QMessageBox.critical(self, "Error", "No stack selected.")
            return

        # Open file dialog
        selected_file = self._get_file_name("Log to be loaded", "Log File (*.txt *.log *.csv)")

        # Cancel/Close was clicked
        if selected_file == "":
            return

        self.presenter.add_log_to_sample(stack_id=stack_to_add_log_to, log_file=Path(selected_file))

        QMessageBox.information(self, "Load complete",
                                f"{selected_file} was loaded as a log into {stack_to_add_log_to}.")

    def load_shuttercounts_dialog(self) -> None:
        stack_selector = DatasetSelectorDialog(main_window=self,
                                               title="Stack Selector",
                                               message="Which stack is the shutter count file being loaded for?",
                                               show_stacks=True)
        # Was closed without accepting (e.g. via x button or ESC)
        if QDialog.DialogCode.Accepted != stack_selector.exec():
            return
        stack_to_add_shuttercounts_to = stack_selector.selected_id

        if stack_to_add_shuttercounts_to is None:
            QMessageBox.critical(self, "Error", "No stack selected.")
            return

        # Open file dialog
        selected_file = self._get_file_name("Shutter count file to be loaded", "Shutter count File (*.txt *.csv)")

        # Cancel/Close was clicked
        if selected_file == "":
            return

        self.presenter.add_shuttercounts_to_sample(stack_id=stack_to_add_shuttercounts_to,
                                                   shuttercount_file=Path(selected_file))
        QMessageBox.information(
            self, "Load complete",
            f"{selected_file} was loaded as a shutter count file into {stack_to_add_shuttercounts_to}.")
        if self.spectrum_viewer:
            self.spectrum_viewer.handle_shuttercount_change()

    def load_180_deg_dialog(self) -> None:
        dataset_selector = DatasetSelectorDialog(main_window=self,
                                                 title="Dataset Selector",
                                                 message="Which dataset is the 180 projection being loaded for?")
        # Was closed without accepting (e.g. via x button or ESC)
        if QDialog.DialogCode.Accepted != dataset_selector.exec():
            return
        dataset_to_add_180_deg_to = dataset_selector.selected_id

        if dataset_to_add_180_deg_to is None:
            QMessageBox.critical(self, "Error", "No dataset selected.")
            return

        # Open file dialog
        selected_file = self._get_file_name("180 Degree Image", "Image File (*.tif *.tiff)")

        # Cancel/Close was clicked
        if selected_file == "":
            return

        self.presenter.add_180_deg_file_to_dataset(dataset_id=dataset_to_add_180_deg_to, _180_deg_file=selected_file)

    LOAD_PROJECTION_ANGLES_DIALOG_MESSAGE = "Which stack are the projection angles in DEGREES being loaded for?"
    LOAD_PROJECTION_ANGLES_FILE_DIALOG_CAPTION = "File with projection angles in DEGREES"

    def load_projection_angles(self) -> None:
        stack_selector = DatasetSelectorDialog(main_window=self,
                                               title="Stack Selector",
                                               message=self.LOAD_PROJECTION_ANGLES_DIALOG_MESSAGE,
                                               show_stacks=True)
        # Was closed without accepting (e.g. via x button or ESC)
        if QDialog.DialogCode.Accepted != stack_selector.exec():
            return

        stack_id = stack_selector.selected_id

        if stack_id is None:
            QMessageBox.critical(self, "Error", "No stack selected.")
            return

        selected_file = self._get_file_name(self.LOAD_PROJECTION_ANGLES_FILE_DIALOG_CAPTION)
        if selected_file == "":
            return

        pafp = ProjectionAngleFileParser(selected_file)
        projection_angles = pafp.get_projection_angles()

        self.presenter.add_projection_angles_to_sample(stack_id, projection_angles)
        QMessageBox.information(self, "Load complete", f"Angles from {selected_file} were loaded into "
                                f"{stack_id}.")

    def execute_image_file_save(self) -> None:
        self.presenter.notify(PresNotification.IMAGE_FILE_SAVE)

    def execute_image_file_load(self) -> None:
        self.presenter.notify(PresNotification.IMAGE_FILE_LOAD)

    def execute_nexus_load(self) -> None:
        self.presenter.notify(PresNotification.NEXUS_LOAD)

    def execute_nexus_save(self) -> None:
        self.presenter.notify(PresNotification.NEXUS_SAVE)

    def execute_add_to_dataset(self) -> None:
        self.presenter.notify(PresNotification.DATASET_ADD)

    def execute_move_stack(self, origin_dataset_id: uuid.UUID, stack_id: uuid.UUID, destination_stack_type: str,
                           destination_dataset_id: uuid.UUID) -> None:
        self.presenter.notify(PresNotification.MOVE_STACK,
                              origin_dataset_id=origin_dataset_id,
                              stack_id=stack_id,
                              destination_stack_type=destination_stack_type,
                              destination_dataset_id=destination_dataset_id)

    def show_image_save_dialog(self) -> None:
        self.image_save_dialog = ImageSaveDialog(self, self.stack_list)
        self.image_save_dialog.show()

    def show_nexus_save_dialog(self) -> None:
        self.nexus_save_dialog = NexusSaveDialog(self, self.presenter.datasets)
        self.nexus_save_dialog.show()

    def show_settings_window(self) -> None:
        if not self.settings_window:
            self.settings_window = SettingsWindowView(self)
            self.settings_window.show()
        else:
            self.settings_window.activateWindow()
            self.settings_window.raise_()
            self.settings_window.show()

    def show_recon_window(self) -> None:
        if not self.recon:
            self.recon = ReconstructWindowView(self)
            self.recon.show()
        else:
            self.recon.activateWindow()
            self.recon.raise_()
            self.recon.show()

    def show_filters_window(self) -> None:
        if not self.filters:
            self.filters = FiltersWindowView(self)
            self.filters.filter_applied.connect(self.stack_changed.emit)
            self.filters.show()
        else:
            self.filters.activateWindow()
            self.filters.raise_()

    def show_spectrum_viewer_window(self) -> None:
        if not self.spectrum_viewer:
            self.spectrum_viewer = SpectrumViewerWindowView(self)
            self.spectrum_viewer.show()
        else:
            self.spectrum_viewer.activateWindow()
            self.spectrum_viewer.raise_()
            self.spectrum_viewer.show()

    def live_view_choose_directory(self) -> None:
        caption = "Choose live data directory"
        live_data_directory: str = QFileDialog.getExistingDirectory(self,
                                                                    caption=caption,
                                                                    options=QFileDialog.ShowDirsOnly)
        if live_data_directory != "":
            self.show_live_viewer(Path(live_data_directory))

    def show_live_viewer(self, live_data_path: Path) -> None:
        if not self.live_viewer:
            self.live_viewer = LiveViewerWindowView(self, live_data_path)
            self.live_viewer.show()
        else:
            self.live_viewer.activateWindow()
            self.live_viewer.raise_()
            self.live_viewer.show()

    @property
    def stack_list(self) -> list[StackId]:
        return self.presenter.stack_visualiser_list

    @property
    def stack_names(self) -> list[str]:
        return self.presenter.stack_visualiser_names

    def get_stack_visualiser(self, stack_uuid) -> StackVisualiserView:
        return self.presenter.get_stack_visualiser(stack_uuid)

    def get_stack(self, stack_uuid: uuid.UUID) -> ImageStack:
        return self.presenter.get_stack(stack_uuid)

    def get_images_from_stack_uuid(self, stack_uuid) -> ImageStack:
        return self.presenter.get_stack_visualiser(stack_uuid).presenter.images

    def get_dataset_id_from_stack_uuid(self, stack_id: uuid.UUID) -> uuid.UUID:
        return self.presenter.get_dataset_id_for_stack(stack_id)

    def get_dataset(self, dataset_id: uuid.UUID) -> Dataset | None:
        return self.presenter.get_dataset(dataset_id)

    def get_all_stacks(self) -> list[ImageStack]:
        return self.presenter.get_all_stacks()

    def get_all_180_projections(self) -> list[ImageStack]:
        return self.presenter.get_all_180_projections()

    def get_stack_history(self, stack_uuid) -> dict[str, Any]:
        return self.presenter.get_stack_visualiser_history(stack_uuid)

    def create_new_stack(self, images: ImageStack) -> None:
        self.presenter.create_single_tabbed_images_stack(images)

    def get_stack_with_images(self, images: ImageStack) -> StackVisualiserView:
        return self.presenter.get_stack_with_images(images)

    def create_stack_window(self,
                            stack: ImageStack,
                            position: Qt.DockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea,
                            floating: bool = False) -> StackVisualiserView:
        stack.make_name_unique(self.stack_names)
        stack_vis = StackVisualiserView(self, stack)

        # this puts the new stack window into the centre of the window
        self.splitter.addWidget(stack_vis)
        self.setCentralWidget(self.splitter)

        # add the dock widget into the main window
        self.addDockWidget(position, stack_vis)

        stack_vis.setFloating(floating)

        self.presenter.add_stack_to_dictionary(stack_vis)
        return stack_vis

    def rename_stack(self, current_name: str, new_name: str) -> None:
        self.presenter.notify(PresNotification.RENAME_STACK, current_name=current_name, new_name=new_name)

    def closeEvent(self, event) -> None:
        """
        Handles a request to quit the application from the user.
        """
        should_close = True

        if self.presenter.have_active_stacks and self.open_dialogs:
            # Show confirmation box asking if the user really wants to quit if
            # they have data loaded
            msg_box = QMessageBox.question(self,
                                           "Quit",
                                           "Are you sure you want to quit with loaded data?",
                                           defaultButton=QMessageBox.No)
            should_close = msg_box == QMessageBox.Yes

        if should_close:
            # Pass close event to parent
            super().closeEvent(event)
            # Close additional windows which do not have the MainWindow as parent
            if self.recon:
                self.recon.close()
            if self.live_viewer:
                self.live_viewer.close()
            if self.spectrum_viewer:
                self.spectrum_viewer.close()
            if self.filters:
                self.filters.close()
            if self.settings_window:
                self.settings_window.close()

        else:
            # Ignore the close event, keeping window open
            event.ignore()

    def cleanup(self) -> None:
        # Release shared memory from loaded stacks
        for stack in self.get_all_stacks():
            stack.shared_array = None  # type: ignore # Only happens when cleaning up

    def uncaught_exception(self, user_error_msg: str, log_error_msg: str) -> None:
        getLogger(__name__).error(log_error_msg)
        self.show_error_dialog(f"Uncaught exception {user_error_msg}")

    from uuid import UUID

    def show_stack_select_dialog(self) -> StackComparePresenter | None:
        dialog = MultipleStackSelect(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            stack_one_id: UUID | None = dialog.stack_one.current()
            stack_two_id: UUID | None = dialog.stack_two.current()

            if stack_one_id is not None and stack_two_id is not None:
                one = self.presenter.get_stack(stack_one_id)
                two = self.presenter.get_stack(stack_two_id)

                stack_choice: StackComparePresenter = StackComparePresenter(one, two, self)
                stack_choice.show()

                return stack_choice
        return None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if not os.path.exists(file_path):
                continue
            if os.path.isdir(file_path):
                sample_loading = self.show_image_load_dialog_with_path(file_path)
                if not sample_loading:
                    QMessageBox.critical(
                        self, "Load not possible!", "Please provide a directory that has .tif or .tiff files in it, or "
                        "a sub directory that do not contain dark, flat, or 180 in their title name, that represents a"
                        " sample.")
                    return
            else:
                QMessageBox.critical(self, "Load not possible!", "Please drag and drop only folders/directories!")
                return

    def ask_to_use_closest_to_180(self, diff_rad: float) -> bool:
        """
        Asks the user if they want to use the projection that is closest to 180 degrees as the 180deg.
        :param diff_rad: The difference from the closest projection to 180 in radians.
        :return: True if the answer wants to use the closest projection, False otherwise.
        """
        diff_deg = round(np.rad2deg(diff_rad), 2)
        return QMessageBox.Yes == QMessageBox.question(
            self, "180 Projection",
            f"Unable to find a 180 degree projection. The closest projection is {str(diff_deg)} degrees away from 180. "
            f"Use anyway?")

    def clear_dataset_tree_widget(self) -> None:
        self.dataset_tree_widget.clear()

    def add_toplevel_item_to_dataset_tree_widget(self, title: str, id: uuid.UUID) -> QTreeDatasetWidgetItem:
        item = self.new_dataset_tree_widget_item(title, id, self.dataset_tree_widget)
        return item

    def add_item_to_dataset_tree_widget(self, title: str, id: uuid.UUID,
                                        parent_item: QTreeDatasetWidgetItem) -> QTreeDatasetWidgetItem:
        item = self.new_dataset_tree_widget_item(title, id, parent_item)
        parent_item.setExpanded(True)
        return item

    @staticmethod
    def new_dataset_tree_widget_item(title: str, id: uuid.UUID,
                                     parent_item: QTreeDatasetWidgetItem | QTreeWidget) -> QTreeDatasetWidgetItem:
        dataset_tree_item = QTreeDatasetWidgetItem(parent_item, id)
        dataset_tree_item.setText(0, title)
        return dataset_tree_item

    def create_dataset_tree_widget_item(self, title: str, id: uuid.UUID) -> QTreeDatasetWidgetItem:
        dataset_tree_item = QTreeDatasetWidgetItem(self.dataset_tree_widget, id)
        dataset_tree_item.setText(0, title)
        return dataset_tree_item

    @staticmethod
    def create_child_tree_item(parent: QTreeDatasetWidgetItem, dataset_id: uuid.UUID, name: str) -> None:
        child = QTreeDatasetWidgetItem(parent, dataset_id)
        child.setText(0, name)
        parent.addChild(child)

    @staticmethod
    def get_sinograms_item(parent: QTreeDatasetWidgetItem) -> QTreeDatasetWidgetItem | None:
        """
        Tries to look for a sinograms entry in a dataset tree view item.
        :return: The sinograms entry if found, None otherwise.
        """
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0) == SINO_TEXT:
                return child
        return None

    def add_item_to_tree_view(self, item: QTreeWidgetItem) -> None:
        self.dataset_tree_widget.insertTopLevelItem(self.dataset_tree_widget.topLevelItemCount(), item)
        item.setExpanded(True)

    def _open_tree_menu(self, position: QPoint) -> None:
        """
        Opens the tree view menu.
        :param position: The position of the cursor when the menu was opened relative to the main window.
        """
        self.menuTreeView = QMenu()

        add_action = self.menuTreeView.addAction("Add / Replace Stack")
        add_action.triggered.connect(self._add_images_to_existing_dataset)

        if self.dataset_tree_widget.itemAt(position).id in self.presenter.all_stack_ids:
            move_action = self.menuTreeView.addAction("Move Stack")
            move_action.triggered.connect(self._move_stack)

        delete_action = self.menuTreeView.addAction("Delete")
        delete_action.triggered.connect(self._delete_container)

        self.menuTreeView.exec_(self.dataset_tree_widget.viewport().mapToGlobal(position))

    def _delete_container(self) -> None:
        """
        Sends the signal to the presenter to delete data corresponding with an item on the dataset tree view.
        """
        container_id = self.dataset_tree_widget.selectedItems()[0].id
        self.presenter.notify(PresNotification.REMOVE_STACK, container_id=container_id)

    def _add_images_to_existing_dataset(self) -> None:
        """
        Notifies presenter to add image stack of dataset of the selected item.
        """
        container_id = self.dataset_tree_widget.selectedItems()[0].id
        self.presenter.notify(PresNotification.SHOW_ADD_STACK_DIALOG, container_id=container_id)

    def _move_stack(self) -> None:
        stack_id = self.dataset_tree_widget.selectedItems()[0].id
        self.presenter.notify(PresNotification.SHOW_MOVE_STACK_DIALOG, stack_id=stack_id)

    def _bring_stack_tab_to_front(self, item: QTreeDatasetWidgetItem) -> None:
        """
        Sends the signal to the presenter to bring a make a stack tab visible and bring it to the front.
        :param item: The QTreeDatasetWidgetItem that was clicked.
        """
        self.presenter.notify(PresNotification.FOCUS_TAB, stack_id=item.id)

    def add_recon_to_dataset(self, recon_data: ImageStack, stack_id: uuid.UUID) -> None:
        self.presenter.notify(PresNotification.ADD_RECON, recon_data=recon_data, stack_id=stack_id)

    @staticmethod
    def add_recon_group(dataset_item: QTreeDatasetWidgetItem, recon_id: uuid.UUID) -> QTreeDatasetWidgetItem:
        """
        Adds a recon group to a dataset item in the tree view.
        :param dataset_item: The dataset item.
        :return: The recon group that was added.
        """
        recon_group = QTreeDatasetWidgetItem(dataset_item, recon_id)
        recon_group.setText(0, RECON_GROUP_TEXT)
        dataset_item.addChild(recon_group)
        recon_group.setExpanded(True)
        return recon_group

    @staticmethod
    def get_recon_group(dataset_item: QTreeDatasetWidgetItem) -> QTreeDatasetWidgetItem | None:
        """
        Looks for an existing recon group in a dataset tree view item.
        :param dataset_item: The dataset item to look for the recon group in.
        :return: The recon group if found.
        """
        for i in range(dataset_item.childCount()):
            if dataset_item.child(i).text(0) == RECON_GROUP_TEXT:
                return dataset_item.child(i)
        return None

    def get_dataset_tree_view_item(self, dataset_id: uuid.UUID) -> QTreeDatasetWidgetItem:
        """
        Looks for the dataset tree view item matching a given ID.
        :param dataset_id: The dataset ID.
        :return: The tree view item if found.
        """
        top_level_item_count = self.dataset_tree_widget.topLevelItemCount()
        for i in range(top_level_item_count):
            top_level_item = self.dataset_tree_widget.topLevelItem(i)
            if top_level_item.id == dataset_id:
                return top_level_item
        raise RuntimeError(f"Unable to find dataset with ID {dataset_id}")

    @property
    def sino_text(self) -> str:
        """
        :return: The sinogram entry text. Used to avoid circular imports.
        """
        return SINO_TEXT

    def show_add_stack_to_existing_dataset_dialog(self, dataset_id: uuid.UUID) -> None:
        """
        Displays the dialog for adding an image stack to an existing dataset.
        :param dataset_id: The ID of the dataset to update.
        """
        dataset = self.presenter.get_dataset(dataset_id)
        if dataset is None:
            raise RuntimeError(f"Unable to find dataset with ID {dataset_id}")
        self.add_to_dataset_dialog = AddImagesToDatasetDialog(self, dataset_id, dataset.name)
        self.add_to_dataset_dialog.show()

    def _on_tab_bar_clicked(self, stack: StackVisualiserView) -> None:
        self.presenter.notify(Notification.TAB_CLICKED, stack=stack)

    def show_move_stack_dialog(self, origin_dataset_id: uuid.UUID, stack_id: uuid.UUID, origin_dataset_name: str,
                               stack_data_type: str) -> None:
        self.move_stack_dialog = MoveStackDialog(self, origin_dataset_id, stack_id, origin_dataset_name,
                                                 stack_data_type)
        self.move_stack_dialog.show()

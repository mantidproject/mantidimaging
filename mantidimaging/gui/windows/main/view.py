# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
import uuid
from logging import getLogger
from pathlib import Path
from typing import Optional, List, Union, TYPE_CHECKING, Dict
from uuid import UUID

import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QPoint
from PyQt5.QtGui import QIcon, QDragEnterEvent, QDropEvent, QDesktopServices
from PyQt5.QtWidgets import QAction, QDialog, QLabel, QMessageBox, QMenu, QFileDialog, QSplitter, \
    QTreeWidgetItem, QTreeWidget

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset
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
from mantidimaging.gui.windows.main.presenter import MainWindowPresenter, Notification
from mantidimaging.gui.windows.main.presenter import Notification as PresNotification
from mantidimaging.gui.windows.main.image_save_dialog import ImageSaveDialog
from mantidimaging.gui.windows.move_stack_dialog.view import MoveStackDialog
from mantidimaging.gui.windows.nexus_load_dialog.view import NexusLoadDialog
from mantidimaging.gui.windows.operations import FiltersWindowView
from mantidimaging.gui.windows.recon import ReconstructWindowView
from mantidimaging.gui.windows.spectrum_viewer.view import SpectrumViewerWindowView
from mantidimaging.gui.windows.stack_choice.compare_presenter import StackComparePresenter
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView
from mantidimaging.gui.windows.welcome_screen.presenter import WelcomeScreenPresenter
from mantidimaging.gui.windows.wizard.presenter import WizardPresenter

if TYPE_CHECKING:
    from mantidimaging.core.data.dataset import MixedDataset

RECON_GROUP_TEXT = "Recons"
SINO_TEXT = "Sinograms"

LOG = getLogger(__file__)


class QTreeDatasetWidgetItem(QTreeWidgetItem):
    def __init__(self, parent: QTreeWidget, dataset_id: UUID):
        self._id = dataset_id
        super().__init__(parent)

    @property
    def id(self):
        return self._id


class MainWindowView(BaseMainWindowView):
    NOT_THE_LATEST_VERSION = "This is not the latest version"
    UNCAUGHT_EXCEPTION = "Uncaught exception"

    # Emitted when a new stack is created or an existing one deleted
    model_changed = pyqtSignal()
    # Emitted when an existing stack is changed
    stack_changed = pyqtSignal()
    backend_message = pyqtSignal(bytes)

    menuFile: QMenu
    menuWorkflow: QMenu
    menuImage: QMenu
    menuHelp: QMenu
    menuTreeView: Optional[QMenu] = None

    actionRecon: QAction
    actionFilters: QAction
    actionCompareImages: QAction
    actionSpectrumViewer: QAction
    actionSampleLoadLog: QAction
    actionLoadProjectionAngles: QAction
    actionLoad180deg: QAction
    actionLoadDataset: QAction
    actionLoadImages: QAction
    actionLoadNeXusFile: QAction
    actionSaveImages: QAction
    actionSaveNeXusFile: QAction
    actionExit: QAction

    filters: Optional[FiltersWindowView] = None
    recon: Optional[ReconstructWindowView] = None
    spectrum_viewer: Optional[SpectrumViewerWindowView] = None

    image_load_dialog: Optional[ImageLoadDialog] = None
    image_save_dialog: Optional[ImageSaveDialog] = None
    nexus_load_dialog: Optional[NexusLoadDialog] = None
    nexus_save_dialog: Optional[NexusSaveDialog] = None
    add_to_dataset_dialog: Optional[AddImagesToDatasetDialog] = None
    move_stack_dialog: Optional[MoveStackDialog] = None

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
            if versions.get_conda_installed_label() != "main":
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

        args = CommandLineArguments()
        if args.path():
            self.presenter.load_stacks_from_folder(args.path())

        if args.operation():
            self.presenter.show_operation(args.operation())

        if args.recon():
            self.show_recon_window()

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

    def setup_shortcuts(self):
        self.actionLoadDataset.triggered.connect(self.show_image_load_dialog)
        self.actionLoadImages.triggered.connect(self.load_image_stack)
        self.actionLoadNeXusFile.triggered.connect(self.show_nexus_load_dialog)
        self.actionSampleLoadLog.triggered.connect(self.load_sample_log_dialog)
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

        self.actionCompareImages.triggered.connect(self.show_stack_select_dialog)

        self.model_changed.connect(self.update_shortcuts)

    def populate_image_menu(self):
        self.menuImage.clear()
        current_stack = self.current_showing_stack()
        if current_stack is None:
            self.menuImage.addAction("No stack loaded!")
        else:
            populate_menu(self.menuImage, current_stack.actions)

    def current_showing_stack(self) -> Optional[StackVisualiserView]:
        for stack in self.findChildren(StackVisualiserView):
            if not stack.visibleRegion().isEmpty():
                return stack
        return None

    def update_shortcuts(self):
        has_datasets = len(self.presenter.datasets) > 0
        has_strict_datasets = any(isinstance(dataset, StrictDataset) for dataset in self.presenter.datasets)

        self.actionSaveImages.setEnabled(has_datasets)
        self.actionSaveNeXusFile.setEnabled(has_strict_datasets)
        self.actionSampleLoadLog.setEnabled(has_datasets)
        self.actionLoad180deg.setEnabled(has_strict_datasets)
        self.actionLoadProjectionAngles.setEnabled(has_datasets)
        self.menuWorkflow.setEnabled(has_datasets)
        self.menuImage.setEnabled(has_datasets)

    @staticmethod
    def open_online_documentation():
        url = QUrl("https://mantidproject.github.io/mantidimaging/")
        QDesktopServices.openUrl(url)

    def show_about(self):
        self.welcome_window = WelcomeScreenPresenter(self)
        self.welcome_window.show()

    def show_image_load_dialog(self):
        self.image_load_dialog = ImageLoadDialog(self)
        self.image_load_dialog.show()

    def show_nexus_load_dialog(self):
        self.nexus_load_dialog = NexusLoadDialog(self)
        self.nexus_load_dialog.show()

    def show_wizard(self):
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

    def load_image_stack(self):
        # Open file dialog
        selected_file = self._get_file_name("Image", "Image File (*.tif *.tiff)")

        # Cancel/Close was clicked
        if selected_file == "":
            return

        self.presenter.load_image_stack(selected_file)

    def load_sample_log_dialog(self):
        stack_selector = DatasetSelectorDialog(main_window=self,
                                               title="Stack Selector",
                                               message="Which stack is the log being loaded for?",
                                               show_stacks=True)
        # Was closed without accepting (e.g. via x button or ESC)
        if QDialog.DialogCode.Accepted != stack_selector.exec():
            return
        stack_to_add_log_to = stack_selector.selected_id

        # Open file dialog
        selected_file = self._get_file_name("Log to be loaded", "Log File (*.txt *.log *.csv)")

        # Cancel/Close was clicked
        if selected_file == "":
            return

        self.presenter.add_log_to_sample(stack_id=stack_to_add_log_to, log_file=Path(selected_file))

        QMessageBox.information(self, "Load complete", f"{selected_file} was loaded as a log into "
                                f"{stack_to_add_log_to}.")

    def load_180_deg_dialog(self):
        dataset_selector = DatasetSelectorDialog(main_window=self,
                                                 title="Dataset Selector",
                                                 message="Which dataset is the 180 projection being loaded for?")
        # Was closed without accepting (e.g. via x button or ESC)
        if QDialog.DialogCode.Accepted != dataset_selector.exec():
            return
        dataset_to_add_180_deg_to = dataset_selector.selected_id

        # Open file dialog
        selected_file = self._get_file_name("180 Degree Image", "Image File (*.tif *.tiff)")

        # Cancel/Close was clicked
        if selected_file == "":
            return

        self.presenter.add_180_deg_file_to_dataset(dataset_id=dataset_to_add_180_deg_to, _180_deg_file=selected_file)

    LOAD_PROJECTION_ANGLES_DIALOG_MESSAGE = "Which stack are the projection angles in DEGREES being loaded for?"
    LOAD_PROJECTION_ANGLES_FILE_DIALOG_CAPTION = "File with projection angles in DEGREES"

    def load_projection_angles(self):
        stack_selector = DatasetSelectorDialog(main_window=self,
                                               title="Stack Selector",
                                               message=self.LOAD_PROJECTION_ANGLES_DIALOG_MESSAGE,
                                               show_stacks=True)
        # Was closed without accepting (e.g. via x button or ESC)
        if QDialog.DialogCode.Accepted != stack_selector.exec():
            return

        stack_id = stack_selector.selected_id

        selected_file = self._get_file_name(self.LOAD_PROJECTION_ANGLES_FILE_DIALOG_CAPTION)
        if selected_file == "":
            return

        pafp = ProjectionAngleFileParser(selected_file)
        projection_angles = pafp.get_projection_angles()

        self.presenter.add_projection_angles_to_sample(stack_id, projection_angles)
        QMessageBox.information(self, "Load complete", f"Angles from {selected_file} were loaded into into "
                                f"{stack_id}.")

    def execute_image_file_save(self):
        self.presenter.notify(PresNotification.IMAGE_FILE_SAVE)

    def execute_image_file_load(self):
        self.presenter.notify(PresNotification.IMAGE_FILE_LOAD)

    def execute_nexus_load(self):
        self.presenter.notify(PresNotification.NEXUS_LOAD)

    def execute_nexus_save(self):
        self.presenter.notify(PresNotification.NEXUS_SAVE)

    def execute_add_to_dataset(self):
        self.presenter.notify(PresNotification.DATASET_ADD)

    def execute_move_stack(self, origin_dataset_id: uuid.UUID, stack_id: uuid.UUID, destination_data_type: str,
                           destination_dataset_name: str):
        self.presenter.notify(PresNotification.MOVE_STACK,
                              origin_dataset_id=origin_dataset_id,
                              stack_id=stack_id,
                              destination_data_type=destination_data_type,
                              destination_dataset_name=destination_dataset_name)

    def show_image_save_dialog(self):
        self.image_save_dialog = ImageSaveDialog(self, self.stack_list)
        self.image_save_dialog.show()

    def show_nexus_save_dialog(self):
        self.nexus_save_dialog = NexusSaveDialog(self, self.strict_dataset_list)
        self.nexus_save_dialog.show()

    def show_recon_window(self):
        if not self.recon:
            self.recon = ReconstructWindowView(self)
            self.recon.show()
        else:
            self.recon.activateWindow()
            self.recon.raise_()
            self.recon.show()

    def show_filters_window(self):
        if not self.filters:
            self.filters = FiltersWindowView(self)
            self.filters.filter_applied.connect(self.stack_changed.emit)
            self.filters.show()
        else:
            self.filters.activateWindow()
            self.filters.raise_()

    def show_spectrum_viewer_window(self):
        if not self.spectrum_viewer:
            self.spectrum_viewer = SpectrumViewerWindowView(self)
            self.spectrum_viewer.show()
        else:
            self.spectrum_viewer.activateWindow()
            self.spectrum_viewer.raise_()
            self.spectrum_viewer.show()

    @property
    def stack_list(self):
        return self.presenter.stack_visualiser_list

    @property
    def strict_dataset_list(self):
        return self.presenter.strict_dataset_list

    @property
    def stack_names(self):
        return self.presenter.stack_visualiser_names

    def get_stack_visualiser(self, stack_uuid):
        return self.presenter.get_stack_visualiser(stack_uuid)

    def get_stack(self, stack_uuid: uuid.UUID) -> ImageStack:
        return self.presenter.get_stack(stack_uuid)

    def get_images_from_stack_uuid(self, stack_uuid) -> ImageStack:
        return self.presenter.get_stack_visualiser(stack_uuid).presenter.images

    def get_dataset_id_from_stack_uuid(self, stack_id: uuid.UUID) -> uuid.UUID:
        return self.presenter.get_dataset_id_for_stack(stack_id)

    def get_dataset(self, dataset_id: uuid.UUID) -> Optional[Union['MixedDataset', StrictDataset]]:
        return self.presenter.get_dataset(dataset_id)

    def get_all_stacks(self) -> List[ImageStack]:
        return self.presenter.get_all_stacks()

    def get_all_180_projections(self):
        return self.presenter.get_all_180_projections()

    def get_stack_history(self, stack_uuid):
        return self.presenter.get_stack_visualiser_history(stack_uuid)

    def create_new_stack(self, images: ImageStack):
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

    def rename_stack(self, current_name: str, new_name: str):
        self.presenter.notify(PresNotification.RENAME_STACK, current_name=current_name, new_name=new_name)

    def closeEvent(self, event):
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

        else:
            # Ignore the close event, keeping window open
            event.ignore()

    def cleanup(self):
        # Release shared memory from loaded stacks
        for stack in self.get_all_stacks():
            stack.shared_array = None

    def uncaught_exception(self, user_error_msg, log_error_msg):
        QMessageBox.critical(self, self.UNCAUGHT_EXCEPTION, f"{user_error_msg}")
        getLogger(__name__).error(log_error_msg)

    def show_stack_select_dialog(self):
        dialog = MultipleStackSelect(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            one = self.presenter.get_stack(dialog.stack_one.current())
            two = self.presenter.get_stack(dialog.stack_two.current())

            stack_choice = StackComparePresenter(one, two, self)
            stack_choice.show()

            return stack_choice

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if not os.path.exists(file_path):
                continue
            if os.path.isdir(file_path):
                # Load directory as stack
                sample_loading = self.presenter.load_stacks_from_folder(file_path)
                if not sample_loading:
                    QMessageBox.critical(
                        self, "Load not possible!", "Please provide a directory that has .tif or .tiff files in it, or "
                        "a sub directory that do not contain dark, flat, or 180 in their title name, that represents a"
                        " sample.")
                    return
            else:
                QMessageBox.critical(self, "Load not possible!", "Please drag and drop only folders/directories!")
                return

    def ask_to_use_closest_to_180(self, diff_rad: float):
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

    def create_dataset_tree_widget_item(self, title: str, id: uuid.UUID) -> QTreeDatasetWidgetItem:
        dataset_tree_item = QTreeDatasetWidgetItem(self.dataset_tree_widget, id)
        dataset_tree_item.setText(0, title)
        return dataset_tree_item

    @staticmethod
    def create_child_tree_item(parent: QTreeDatasetWidgetItem, dataset_id: uuid.UUID, name: str):
        child = QTreeDatasetWidgetItem(parent, dataset_id)
        child.setText(0, name)
        parent.addChild(child)

    @staticmethod
    def get_sinograms_item(parent: QTreeDatasetWidgetItem) -> Optional[QTreeDatasetWidgetItem]:
        """
        Tries to look for a sinograms entry in a dataset tree view item.
        :return: The sinograms entry if found, None otherwise.
        """
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0) == SINO_TEXT:
                return child
        return None

    def add_item_to_tree_view(self, item: QTreeWidgetItem):
        self.dataset_tree_widget.insertTopLevelItem(self.dataset_tree_widget.topLevelItemCount(), item)
        item.setExpanded(True)

    def _open_tree_menu(self, position: QPoint):
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

    def _delete_container(self):
        """
        Sends the signal to the presenter to delete data corresponding with an item on the dataset tree view.
        """
        container_id = self.dataset_tree_widget.selectedItems()[0].id
        self.presenter.notify(PresNotification.REMOVE_STACK, container_id=container_id)

    def _add_images_to_existing_dataset(self):
        """
        Notifies presenter to add image stack of dataset of the selected item.
        """
        container_id = self.dataset_tree_widget.selectedItems()[0].id
        self.presenter.notify(PresNotification.SHOW_ADD_STACK_DIALOG, container_id=container_id)

    def _move_stack(self):
        stack_id = self.dataset_tree_widget.selectedItems()[0].id
        self.presenter.notify(PresNotification.SHOW_MOVE_STACK_DIALOG, stack_id=stack_id)

    def _bring_stack_tab_to_front(self, item: QTreeDatasetWidgetItem):
        """
        Sends the signal to the presenter to bring a make a stack tab visible and bring it to the front.
        :param item: The QTreeDatasetWidgetItem that was clicked.
        """
        self.presenter.notify(PresNotification.FOCUS_TAB, stack_id=item.id)

    def add_recon_to_dataset(self, recon_data: ImageStack, stack_id: uuid.UUID):
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
    def get_recon_group(dataset_item: QTreeDatasetWidgetItem) -> Optional[QTreeDatasetWidgetItem]:
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

    def show_add_stack_to_existing_dataset_dialog(self, dataset_id: uuid.UUID):
        """
        Displays the dialog for adding an image stack to an existing dataset.
        :param dataset_id: The ID of the dataset to update.
        """
        dataset = self.presenter.get_dataset(dataset_id)
        if dataset is None:
            raise RuntimeError(f"Unable to find dataset with ID {dataset_id}")
        self.add_to_dataset_dialog = AddImagesToDatasetDialog(self, dataset_id, isinstance(dataset, StrictDataset),
                                                              dataset.name)
        self.add_to_dataset_dialog.show()

    def _on_tab_bar_clicked(self, stack: StackVisualiserView):
        self.presenter.notify(Notification.TAB_CLICKED, stack=stack)

    def show_move_stack_dialog(self, dataset_id: uuid.UUID, stack_id: uuid.UUID, dataset_name: str,
                               stack_data_type: str, is_dataset_strict: Dict[str, bool]):
        self.move_stack_dialog = MoveStackDialog(self, dataset_id, stack_id, dataset_name, stack_data_type,
                                                 is_dataset_strict)
        self.move_stack_dialog.show()

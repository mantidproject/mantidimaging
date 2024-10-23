# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import traceback
import uuid
from enum import Enum, auto
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple
from collections.abc import Iterable

import numpy as np
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtWidgets import QTabBar, QApplication, QTreeWidgetItem
from qt_material import apply_stylesheet

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import _get_stack_data_type, Dataset
from mantidimaging.core.io.loader.loader import create_loading_parameters_for_file_path
from mantidimaging.core.io.utility import find_projection_closest_to_180, THRESHOLD_180
from mantidimaging.core.utility.data_containers import ProjectionAngles
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.stack_visualiser.view import StackVisualiserView
from .model import MainWindowModel
from mantidimaging.gui.windows.main.image_save_dialog import ImageSaveDialog

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # pragma: no cover
    from mantidimaging.gui.dialogs.async_task.task import TaskWorkerThread

RECON_TEXT = "Recon"

settings = QSettings('mantidproject', 'Mantid Imaging')


class StackId(NamedTuple):
    id: uuid.UUID
    name: str


logger = getLogger(__name__)


class Notification(Enum):
    IMAGE_FILE_LOAD = auto()
    IMAGE_FILE_SAVE = auto()
    REMOVE_STACK = auto()
    RENAME_STACK = auto()
    NEXUS_LOAD = auto()
    NEXUS_SAVE = auto()
    FOCUS_TAB = auto()
    ADD_RECON = auto()
    SHOW_ADD_STACK_DIALOG = auto()
    DATASET_ADD = auto()
    TAB_CLICKED = auto()
    SHOW_MOVE_STACK_DIALOG = auto()
    MOVE_STACK = auto()


class MainWindowPresenter(BasePresenter):
    LOAD_ERROR_STRING = "Failed to load stack. Error: {}"
    SAVE_ERROR_STRING = "Failed to save data. Error: {}"

    view: MainWindowView

    def __init__(self, view: MainWindowView):
        super().__init__(view)
        self.model = MainWindowModel()
        self.stack_visualisers: dict[uuid.UUID, StackVisualiserView] = {}

    def notify(self, signal: Notification, **baggage):
        try:
            if signal == Notification.IMAGE_FILE_LOAD:
                self.load_image_files()
            elif signal == Notification.IMAGE_FILE_SAVE:
                self.save_image_files()
            elif signal == Notification.REMOVE_STACK:
                self._delete_container(**baggage)
            elif signal == Notification.RENAME_STACK:
                self._do_rename_stack(**baggage)
            elif signal == Notification.NEXUS_LOAD:
                self.load_nexus_file()
            elif signal == Notification.NEXUS_SAVE:
                self.save_nexus_file()
            elif signal == Notification.FOCUS_TAB:
                self._restore_and_focus_tab(**baggage)
            elif signal == Notification.ADD_RECON:
                self._add_recon_to_dataset(**baggage)
            elif signal == Notification.SHOW_ADD_STACK_DIALOG:
                self._show_add_stack_to_dataset_dialog(**baggage)
            elif signal == Notification.DATASET_ADD:
                self.handle_add_images_to_existing_dataset_from_dialog()
            elif signal == Notification.TAB_CLICKED:
                self._on_tab_clicked(**baggage)
            elif signal == Notification.SHOW_MOVE_STACK_DIALOG:
                self._show_move_stack_dialog(**baggage)
            elif signal == Notification.MOVE_STACK:
                self._move_stack(**baggage)

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def _get_stack_visualiser_by_name(self, search_name: str) -> StackVisualiserView | None:
        """
        Uses the stack name to retrieve the QDockWidget object.
        :param search_name: The name of the stack widget to find.
        :return: The QDockWidget if it could be found, None otherwise.
        """
        for stack_id in self.stack_visualiser_list:
            if stack_id.name == search_name:
                return self.active_stacks[stack_id.id]
        return None

    def get_stack_id_by_name(self, search_name: str) -> uuid.UUID | None:
        for stack_id in self.stack_visualiser_list:
            if stack_id.name == search_name:
                return stack_id.id
        return None

    def add_log_to_sample(self, stack_id: uuid.UUID, log_file: Path) -> None:
        self.model.add_log_to_sample(stack_id, log_file)

    def add_shuttercounts_to_sample(self, stack_id: uuid.UUID, shuttercount_file: Path) -> None:
        self.model.add_shutter_counts_to_sample(stack_id, shuttercount_file)

    def _do_rename_stack(self, current_name: str, new_name: str) -> None:
        dock = self._get_stack_visualiser_by_name(current_name)
        if dock is not None:
            dock.setWindowTitle(new_name)
            self.view.model_changed.emit()

    def load_image_files(self) -> None:
        assert self.view.image_load_dialog is not None
        par = self.view.image_load_dialog.get_parameters()

        start_async_task_view(self.view, self.model.do_load_dataset, self._on_dataset_load_done, {'parameters': par})

    def load_nexus_file(self) -> None:
        assert self.view.nexus_load_dialog is not None
        dataset, _ = self.view.nexus_load_dialog.presenter.get_dataset()
        self.model.add_dataset_to_model(dataset)
        self._add_dataset_to_view(dataset)
        self.view.model_changed.emit()

    def save_nexus_file(self) -> None:
        assert self.view.nexus_save_dialog is not None
        dataset_id = self.view.nexus_save_dialog.selected_dataset
        start_async_task_view(self.view,
                              self.model.do_nexus_saving,
                              self._on_save_done, {
                                  'dataset_id': dataset_id,
                                  'path': self.view.nexus_save_dialog.save_path(),
                                  'sample_name': self.view.nexus_save_dialog.sample_name(),
                                  'save_as_float': self.view.nexus_save_dialog.save_as_float
                              },
                              busy=True)

    def load_image_stack(self, file_path: str) -> None:
        start_async_task_view(self.view, self.model.load_images_into_mixed_dataset, self._on_dataset_load_done,
                              {'file_path': file_path})

    def _open_window_if_not_open(self) -> None:
        """
        Launches windows that requires loaded data if the CLI flags are set.
        Resets args after window has opened.
        """
        if self.view.args.operation() != "" and self.view.filters is None:
            self.show_operation(self.view.args.operation())
            self.view.args.clear_window_args()
        if self.view.args.recon() and self.view.recon is None:
            self.view.show_recon_window()
            self.view.args.clear_window_args()
        if self.view.args.spectrum_viewer() and self.view.spectrum_viewer is None:
            self.view.show_spectrum_viewer_window()
            self.view.args.clear_window_args()

    def _on_dataset_load_done(self, task: TaskWorkerThread) -> None:

        if task.was_successful():
            self._add_dataset_to_view(task.result)
            self.view.model_changed.emit()
            task.result = None
            self._open_window_if_not_open()
        else:
            self._handle_task_error(self.LOAD_ERROR_STRING, task)

    def _add_dataset_to_view(self, dataset: Dataset) -> None:
        """
        Takes a loaded dataset and tries to find a substitute 180 projection (if required) then creates the stack window
        and dataset tree view items.
        :param dataset: The loaded dataset.
        """
        self.update_dataset_tree()
        self.create_dataset_stack_visualisers(dataset)
        if dataset.sample:
            self.add_alternative_180_if_required(dataset)

    def _handle_task_error(self, base_message: str, task: TaskWorkerThread) -> None:
        msg = base_message.format(task.error)
        logger.error(msg)
        self.show_error(msg, traceback.format_exc())

    def _create_and_tabify_stack_window(self, images: ImageStack, sample_dock: StackVisualiserView) -> None:
        """
        Creates a new stack window with a given ImageStack object then makes sure it is placed on top of a
        sample/original stack window.
        :param images: The ImageStack object for the new stack window.
        :param sample_dock: The existing stack window that the new one should be placed on top of.
        """
        stack_visualiser = self._create_lone_stack_window(images)
        self._tabify_stack_window(stack_visualiser, sample_dock)

    def get_active_stack_visualisers(self) -> list[StackVisualiserView]:
        return list(self.active_stacks.values())

    def get_all_stacks(self) -> list[ImageStack]:
        return self.model.images

    def get_all_180_projections(self) -> list[ImageStack]:
        return self.model.proj180s

    def add_alternative_180_if_required(self, dataset: Dataset) -> None:
        """
        Checks if the dataset has a 180 projection and tries to find an alternative if one is missing.
        :param dataset: The loaded dataset.
        """
        assert dataset.sample is not None
        if dataset.sample.has_proj180deg() and dataset.sample.proj180deg.filenames:  # type: ignore
            return
        else:
            closest_projection, diff = find_projection_closest_to_180(dataset.sample.projections,
                                                                      dataset.sample.projection_angles().value)
            if diff <= THRESHOLD_180 or self.view.ask_to_use_closest_to_180(diff):
                _180_arr = np.reshape(closest_projection, (1, ) + closest_projection.shape).copy()
                proj180deg = ImageStack(_180_arr, name=f"{dataset.name}_180")
                self.add_images_to_existing_dataset(dataset.id, proj180deg, "proj_180")

    def create_dataset_stack_visualisers(self, dataset: Dataset) -> StackVisualiserView:
        """
        Creates the StackVisualiserView widgets for a new dataset.
        """
        stacks = dataset.all
        first_stack_vis = self._create_lone_stack_window(stacks[0])
        self._tabify_stack_window(first_stack_vis)

        for stack in stacks[1:]:
            self._create_and_tabify_stack_window(stack, first_stack_vis)

        self._focus_on_newest_stack_tab()
        return first_stack_vis

    def _focus_on_newest_stack_tab(self) -> None:
        """
        Focuses on the newest stack when there is more than one being displayed.
        """
        n_stack_visualisers = len(self.get_active_stack_visualisers())
        if n_stack_visualisers <= 1:
            return

        tab_bar = self.view.findChild(QTabBar)
        if tab_bar is not None:
            last_stack_pos = n_stack_visualisers
            # make Qt process the addition of the dock onto the main window
            QApplication.sendPostedEvents()
            tab_bar.setCurrentIndex(last_stack_pos)

    def create_single_tabbed_images_stack(self, images: ImageStack) -> StackVisualiserView:
        """
        Creates a stack for a single ImageStack object and focuses on it.
        :param images: The ImageStack object for the new stack window.
        :return: The new StackVisualiserView.
        """
        stack_vis = self._create_lone_stack_window(images)
        self._tabify_stack_window(stack_vis)
        self._focus_on_newest_stack_tab()
        return stack_vis

    def _create_lone_stack_window(self, images: ImageStack) -> StackVisualiserView:
        """
        Creates a stack window and adds it to the stack list without tabifying.
        :param images: The ImageStack array for the stack window to display.
        :return: The new stack window.
        """
        stack_vis = self.view.create_stack_window(images)
        self.stack_visualisers[stack_vis.id] = stack_vis
        return stack_vis

    def _tabify_stack_window(self,
                             stack_window: StackVisualiserView,
                             tabify_stack: StackVisualiserView | None = None) -> None:
        """
        Places the newly created stack window into a tab.
        :param stack_window: The new stack window.
        :param tabify_stack: The optional existing stack tab that needs to be
        """
        current_stack_visualisers = self.get_active_stack_visualisers()
        if tabify_stack is None and len(current_stack_visualisers) > 0:
            for stack in current_stack_visualisers:
                if stack_window is not stack:
                    self.view.tabifyDockWidget(stack, stack_window)
                    return
        if tabify_stack is not None:
            self.view.tabifyDockWidget(tabify_stack, stack_window)

    def _on_tab_clicked(self, stack: StackVisualiserView) -> None:
        self._set_tree_view_selection_with_id(stack.id)

    def update_dataset_tree(self) -> None:
        self.view.clear_dataset_tree_widget()
        for dataset_id, dataset in self.model.datasets.items():
            dataset_item = self.view.add_toplevel_item_to_dataset_tree_widget(dataset.name, dataset_id)

            attributes = [("Projections", dataset.sample), ("Flat Before", dataset.flat_before),
                          ("Flat After", dataset.flat_after), ("Dark Before", dataset.dark_before),
                          ("Dark After", dataset.dark_after), ("180", dataset.proj180deg),
                          ("Sinograms", dataset.sinograms)]
            for label, item in attributes:
                if item:
                    self.view.add_item_to_dataset_tree_widget(label, item.id, dataset_item)

            if dataset.recons:
                recon_item = self.view.add_item_to_dataset_tree_widget("Recons", dataset.recons.id, dataset_item)
                for recon in dataset.recons:
                    self.view.add_item_to_dataset_tree_widget(recon.name, recon.id, recon_item)

            if dataset.stacks:
                for image_stack in dataset.stacks:
                    self.view.add_item_to_dataset_tree_widget(image_stack.name, image_stack.id, dataset_item)

    def save_image_files(self) -> None:
        assert isinstance(self.view.image_save_dialog, ImageSaveDialog)
        kwargs = {
            'images_id': self.view.image_save_dialog.selected_stack,
            'output_dir': self.view.image_save_dialog.save_path(),
            'name_prefix': self.view.image_save_dialog.name_prefix(),
            'image_format': self.view.image_save_dialog.image_format(),
            'overwrite': self.view.image_save_dialog.overwrite(),
            'pixel_depth': self.view.image_save_dialog.pixel_depth()
        }
        start_async_task_view(self.view, self.model.do_images_saving, self._on_save_done, kwargs)

    def _on_save_done(self, task: TaskWorkerThread) -> None:

        if not task.was_successful():
            self._handle_task_error(self.SAVE_ERROR_STRING, task)

    @property
    def stack_visualiser_list(self) -> list[StackId]:
        stacks = [StackId(stack_id, widget.windowTitle()) for stack_id, widget in self.active_stacks.items()]
        return sorted(stacks, key=lambda x: x.name)

    @property
    def datasets(self) -> Iterable[Dataset]:
        return self.model.datasets.values()

    @property
    def all_dataset_ids(self) -> Iterable[uuid.UUID]:
        return self.model.datasets.keys()

    @property
    def all_stack_ids(self) -> Iterable[uuid.UUID]:
        stack_ids = []
        for ds in self.model.datasets.values():
            stack_ids += ds.all_image_ids
        return stack_ids

    @property
    def stack_visualiser_names(self) -> list[str]:
        return [widget.windowTitle() for widget in self.stack_visualisers.values()]

    def get_dataset(self, dataset_id: uuid.UUID) -> Dataset | None:
        return self.model.datasets.get(dataset_id)

    def get_stack_visualiser(self, stack_id: uuid.UUID) -> StackVisualiserView:
        return self.stack_visualisers[stack_id]

    def get_stack(self, stack_id: uuid.UUID) -> ImageStack:
        images = self.model.get_images_by_uuid(stack_id)
        if images is None:
            raise RuntimeError(f"Stack not found: {stack_id}")
        return images

    def get_stack_visualiser_history(self, stack_id: uuid.UUID) -> dict[str, Any]:
        return self.get_stack_visualiser(stack_id).presenter.images.metadata

    def get_dataset_id_for_stack(self, stack_id: uuid.UUID) -> uuid.UUID:
        return self.model.get_parent_dataset(stack_id)

    @property
    def active_stacks(self) -> dict[uuid.UUID, StackVisualiserView]:
        return {stack_id: stack for (stack_id, stack) in self.stack_visualisers.items() if stack.isVisible()}

    @property
    def have_active_stacks(self) -> bool:
        return len(self.active_stacks) > 0

    def get_stack_with_images(self, images: ImageStack) -> StackVisualiserView:
        for _, sv in self.stack_visualisers.items():
            if images is sv.presenter.images:
                return sv
        raise RuntimeError(f"Did not find stack {images} in stacks! Stacks: {self.stack_visualisers.items()}")

    def add_180_deg_file_to_dataset(self, dataset_id: uuid.UUID, _180_deg_file: str) -> None:
        """
        Loads a 180 file then adds it to the dataset, creates a stack window, and updates the dataset tree view.
        :param dataset_id: The ID of the dataset to update.
        :param _180_deg_file: The filename for the 180 file.
        """
        proj180deg = self.model.add_180_deg_to_dataset(dataset_id, _180_deg_file)
        self.add_images_to_existing_dataset(dataset_id, proj180deg, "proj_180")

    def add_projection_angles_to_sample(self, stack_id: uuid.UUID, proj_angles: ProjectionAngles) -> None:
        self.model.add_projection_angles_to_sample(stack_id, proj_angles)

    def load_stacks_from_folder(self, file_path: str) -> bool:
        loading_params = create_loading_parameters_for_file_path(Path(file_path))
        if loading_params is None:
            return False

        start_async_task_view(self.view, self.model.do_load_dataset, self._on_dataset_load_done,
                              {'parameters': loading_params})
        return True

    def wizard_action_load(self) -> None:
        self.view.show_image_load_dialog()

    def show_operation(self, operation_name: str) -> None:
        self.view.show_filters_window()
        self.view.filters.presenter.set_filter_by_name(operation_name)  # type:ignore[union-attr]

    def wizard_action_show_reconstruction(self) -> None:
        self.view.show_recon_window()

    def remove_item_from_tree_view(self, uuid_remove: uuid.UUID) -> None:
        """
        Removes an item from the tree view using a given ID.
        :param uuid_remove: The ID of the item to remove.
        """
        for i in range(self.view.dataset_tree_widget.topLevelItemCount()):
            top_level_item = self.view.dataset_tree_widget.topLevelItem(i)
            if top_level_item.id == uuid_remove:
                self.view.dataset_tree_widget.takeTopLevelItem(i)
                return

            for j in range(top_level_item.childCount()):
                child_item = top_level_item.child(j)
                if child_item.id == uuid_remove:
                    top_level_item.takeChild(j)
                    return
                if child_item.childCount() > 0:
                    if self._remove_recon_item_from_tree_view(child_item, uuid_remove):
                        if child_item.childCount() == 0:
                            # Delete recon group when last recon item has been removed
                            top_level_item.takeChild(j)
                        return

    def _set_tree_view_selection_with_id(self, uuid_select: uuid.UUID) -> None:
        """
        Selects an item on the tree view using the given ID.
        :param uuid_select: The ID of the item to select.
        """
        for i in range(self.view.dataset_tree_widget.topLevelItemCount()):
            top_level_item = self.view.dataset_tree_widget.topLevelItem(i)
            if top_level_item.id == uuid_select:
                self._select_tree_widget_item(top_level_item)
                return

            for j in range(top_level_item.childCount()):
                child_item = top_level_item.child(j)
                if child_item.id == uuid_select:
                    self._select_tree_widget_item(child_item)
                    return
                if child_item.childCount() > 0:
                    for k in range(child_item.childCount()):
                        recon_item = child_item.child(k)
                        if recon_item.id == uuid_select:
                            self._select_tree_widget_item(recon_item)
                            return

    def _select_tree_widget_item(self, tree_widget_item: QTreeWidgetItem) -> None:
        """
        Clears the existing selection on the dataset tree view and selects a given item.
        :param tree_widget_item: The item to select.
        """
        self.view.dataset_tree_widget.clearSelection()
        tree_widget_item.setSelected(True)

    @staticmethod
    def _remove_recon_item_from_tree_view(recon_group, uuid_remove: uuid.UUID) -> bool:
        """
        Removes a recon item from the recon group in the tree view.
        :param recon_group: The recon group.
        :param uuid_remove: The ID of the recon data to remove.
        :return: True if a recon with a matching ID was removed, False otherwise.
        """
        recon_count = recon_group.childCount()
        for i in range(recon_count):
            recon_item = recon_group.child(i)
            if recon_item.id == uuid_remove:
                recon_group.takeChild(i)
                return True
        return False

    def add_stack_to_dictionary(self, stack: StackVisualiserView) -> None:
        self.stack_visualisers[stack.id] = stack

    def _delete_container(self, container_id: uuid.UUID) -> None:
        """
        Informs the model to delete a container, then updates the view elements.
        :param container_id: The ID of the container to delete.
        """
        # We need the ids of the stacks that have been deleted to tidy up the stack visualiser tabs
        removed_stack_ids = self.model.remove_container(container_id)
        for stack_id in removed_stack_ids:
            if stack_id in self.stack_visualisers:
                self._delete_stack_visualiser(stack_id)

        # If the container_id provided is not a stack id then we remove the entire container from the tree view,
        # otherwise we remove the individual stacks that were deleted
        tree_view_items_to_remove = [container_id] if container_id not in removed_stack_ids else removed_stack_ids
        for item_id in tree_view_items_to_remove:
            self.remove_item_from_tree_view(item_id)

        self.view.model_changed.emit()

    def _delete_stack_visualiser(self, stack_id: uuid.UUID) -> None:
        """
        Deletes a stack and frees memory.
        :param stack_id: The ID of the stack to delete.
        """
        self.stack_visualisers[stack_id].image_view.close()
        self.stack_visualisers[stack_id].presenter.delete_data()
        self.stack_visualisers[stack_id].deleteLater()
        del self.stack_visualisers[stack_id]

    def _restore_and_focus_tab(self, stack_id: uuid.UUID) -> None:
        """
        Makes a stack tab visible and brings it to the front. If dataset ID is given then nothing happens.
        :param stack_id: The ID of the stack tab to focus on.
        """
        if stack_id in self.model.datasets:
            return
        if stack_id in self.model.recon_list_ids:
            return
        if stack_id in self.model.image_ids:
            self.stack_visualisers[stack_id].setVisible(True)
            self.stack_visualisers[stack_id].raise_()
        else:
            raise RuntimeError(f"Unable to find stack with ID {stack_id}")

    def _add_recon_to_dataset(self, recon_data: ImageStack, stack_id: uuid.UUID) -> None:
        """
        Adds a recon to the dataset and tree view and creates a stack image view.
        :param recon_data: The recon data.
        :param stack_id: The ID of one of the stacks in the dataset that the recon data should be added to.
        """
        parent_id = self.model.get_parent_dataset(stack_id)
        self.add_images_to_existing_dataset(parent_id, recon_data, "Recon")

    def add_sinograms_to_dataset_and_update_view(self, sino_stack: ImageStack, original_stack_id: uuid.UUID) -> None:
        """
        Adds sinograms to a dataset or replaces an existing one.
        :param sino_stack: The sinogram stack.
        :param original_stack_id: The ID of a stack in the dataset.
        """
        parent_id = self.model.get_parent_dataset(original_stack_id)
        self.add_images_to_existing_dataset(parent_id, sino_stack, "Sinograms")

    def _show_add_stack_to_dataset_dialog(self, container_id: uuid.UUID) -> None:
        """
        Asks the user to add a stack to a given dataset.
        :param container_id: The ID of the dataset or stack.
        """
        if container_id not in self.all_dataset_ids:
            # get parent ID if selected item is a stack
            container_id = self.get_dataset_id_for_stack(container_id)
        self.view.show_add_stack_to_existing_dataset_dialog(container_id)

    def _show_move_stack_dialog(self, stack_id: uuid.UUID) -> None:
        """
        Shows the move stack dialog.
        :param stack_id: The ID of the stack to move.
        """
        dataset_id = self.get_dataset_id_for_stack(stack_id)
        dataset = self.get_dataset(dataset_id)
        if dataset is None:
            raise RuntimeError(f"Failed to find dataset with ID {dataset_id}")
        stack_data_type = _get_stack_data_type(stack_id, dataset)
        self.view.show_move_stack_dialog(dataset_id, stack_id, dataset.name, stack_data_type)

    def handle_add_images_to_existing_dataset_from_dialog(self) -> None:
        """
        Adds / replaces images to an existing dataset. Updates the tree view and deletes the previous stack if
        necessary.
        """
        assert self.view.add_to_dataset_dialog is not None

        dataset_id = self.view.add_to_dataset_dialog.dataset_id
        new_images = self.view.add_to_dataset_dialog.presenter.images
        images_type = self.view.add_to_dataset_dialog.images_type

        self.add_images_to_existing_dataset(dataset_id, new_images, images_type)

    def add_images_to_existing_dataset(self, dataset_id: uuid.UUID, new_images: ImageStack, images_type: str):
        dataset = self.get_dataset(dataset_id)
        assert dataset is not None
        dataset.set_stack_by_type_name(images_type, new_images)
        self.create_single_tabbed_images_stack(new_images)
        self.update_dataset_tree()
        self._close_unused_visualisers()
        self.view.model_changed.emit()

    def _close_unused_visualisers(self):
        visualisers = set(self.stack_visualisers.keys())
        stacks = {stack.id for stack in self.get_all_stacks()}
        removed = visualisers - stacks
        for stack_id in removed:
            self._delete_stack_visualiser(stack_id)

    def _move_stack(self, origin_dataset_id: uuid.UUID, stack_id: uuid.UUID, destination_stack_type: str,
                    destination_dataset_id: uuid.UUID) -> None:
        """
        Moves a stack from one dataset to another.
        :param origin_dataset_id: The ID of the origin dataset.
        :param stack_id: The ID of the stack to move.
        :param destination_stack_type: The data type the dataset should be when moved.
        :param destination_dataset_id: The ID of the destination dataset.
        """
        origin_dataset = self.get_dataset(origin_dataset_id)
        destination_dataset = self.get_dataset(destination_dataset_id)
        if origin_dataset is None:
            raise RuntimeError(
                f"Unable to find origin dataset with ID {origin_dataset_id} when attempting to move stack")
        if destination_dataset is None:
            raise RuntimeError(
                f"Unable to find destination dataset with ID {destination_dataset_id} when attempting to move stack")

        stack_to_move = self.get_stack(stack_id)
        stack_to_move.name = self._create_strict_dataset_stack_name(destination_stack_type, destination_dataset.name)

        origin_dataset.delete_stack(stack_id)
        self.add_images_to_existing_dataset(destination_dataset_id, stack_to_move, destination_stack_type)

    @staticmethod
    def _create_strict_dataset_stack_name(stack_type: str, dataset_name: str) -> str:
        """
        Creates a name for strict dataset stacks by using the dataset name and the image type.
        :param stack_type: The type of stack in the StrictDataset.
        :param dataset_name: The name of the dataset.
        :return: A string for the stack name.
        """
        return f"{stack_type} {dataset_name}"

    def do_update_UI(self) -> None:
        if settings.value('use_os_defaults', defaultValue='True') == 'True':
            extra_style = settings.value('extra_style_default')
            theme = 'Fusion'
            override_os_theme = 'False'
        else:
            extra_style = settings.value('extra_style')
            use_dark_mode = settings.value('use_dark_mode')
            theme = settings.value('theme_selection')
            override_os_theme = settings.value('override_os_theme')
        os_theme = settings.value('os_theme')
        font = QFont(settings.value('default_font_family'), int(extra_style['font_size'].replace('px', '')))
        app = QApplication.instance()

        app.setFont(font)
        if theme == 'Fusion':
            if override_os_theme == 'False':
                if os_theme == 'Light':
                    self.use_fusion_light_mode()
                elif os_theme == 'Dark':
                    self.use_fusion_dark_mode()
            else:
                if use_dark_mode == 'True':
                    self.use_fusion_dark_mode()
                else:
                    self.use_fusion_light_mode()
            app.setStyle(theme)
            app.setStyleSheet('')
        else:
            apply_stylesheet(app, theme=theme, invert_secondary=False, extra=extra_style)

    @staticmethod
    def use_fusion_dark_mode() -> None:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.black)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.instance().setPalette(palette)

    @staticmethod
    def use_fusion_light_mode() -> None:
        palette = QPalette()
        QApplication.instance().setPalette(palette)

# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import traceback
import uuid
from enum import Enum, auto
from logging import getLogger, Logger
from typing import TYPE_CHECKING, Union, Optional, Dict, List, Any, NamedTuple, Iterable

import numpy as np
from PyQt5.QtWidgets import QTabBar, QApplication

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset, MixedDataset
from mantidimaging.core.io.loader.loader import create_loading_parameters_for_file_path
from mantidimaging.core.io.utility import find_projection_closest_to_180, THRESHOLD_180
from mantidimaging.core.utility.data_containers import ProjectionAngles, LoadingParameters
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.stack_visualiser.view import StackVisualiserView
from .model import MainWindowModel
from mantidimaging.gui.windows.main.image_save_dialog import ImageSaveDialog

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # pragma: no cover
    from mantidimaging.gui.dialogs.async_task.task import TaskWorkerThread


class StackId(NamedTuple):
    id: uuid.UUID
    name: str


class DatasetId(NamedTuple):
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


class MainWindowPresenter(BasePresenter):
    LOAD_ERROR_STRING = "Failed to load stack. Error: {}"
    SAVE_ERROR_STRING = "Failed to save data. Error: {}"

    view: 'MainWindowView'

    def __init__(self, view: 'MainWindowView'):
        super().__init__(view)
        self.model = MainWindowModel()
        self.stack_visualisers: Dict[uuid.UUID, StackVisualiserView] = {}

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
                self._add_images_to_existing_dataset()

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def _get_stack_visualiser_by_name(self, search_name: str) -> Optional[StackVisualiserView]:
        """
        Uses the stack name to retrieve the QDockWidget object.
        :param search_name: The name of the stack widget to find.
        :return: The QDockWidget if it could be found, None otherwise.
        """
        for stack_id in self.stack_visualiser_list:
            if stack_id.name == search_name:
                return self.active_stacks[stack_id.id]
        return None

    def get_stack_id_by_name(self, search_name: str) -> Optional[uuid.UUID]:
        for stack_id in self.stack_visualiser_list:
            if stack_id.name == search_name:
                return stack_id.id
        return None

    def add_log_to_sample(self, stack_id: uuid.UUID, log_file: str) -> None:
        self.model.add_log_to_sample(stack_id, log_file)

    def _do_rename_stack(self, current_name: str, new_name: str) -> None:
        dock = self._get_stack_visualiser_by_name(current_name)
        if dock is not None:
            dock.setWindowTitle(new_name)
            self.view.model_changed.emit()

    def load_image_files(self, par: Optional[LoadingParameters] = None) -> None:
        if par is None:
            assert self.view.image_load_dialog is not None
            par = self.view.image_load_dialog.get_parameters()

        start_async_task_view(self.view, self.model.do_load_dataset, self._on_dataset_load_done, {'parameters': par})

    def load_nexus_file(self) -> None:
        assert self.view.nexus_load_dialog is not None
        dataset, _ = self.view.nexus_load_dialog.presenter.get_dataset()
        self.model.add_dataset_to_model(dataset)
        self._add_strict_dataset_to_view(dataset)
        self.view.model_changed.emit()

    def save_nexus_file(self):
        assert self.view.nexus_save_dialog is not None
        dataset_id = self.view.nexus_save_dialog.selected_dataset
        start_async_task_view(self.view,
                              self.model.do_nexus_saving,
                              self._on_save_done, {
                                  'dataset_id': dataset_id,
                                  'path': self.view.nexus_save_dialog.save_path(),
                                  'sample_name': self.view.nexus_save_dialog.sample_name()
                              },
                              busy=True)

    def load_image_stack(self, file_path: str) -> None:
        start_async_task_view(self.view, self.model.load_images_into_mixed_dataset, self._on_stack_load_done,
                              {'file_path': file_path})

    def _on_stack_load_done(self, task: 'TaskWorkerThread') -> None:
        log = getLogger(__name__)

        if task.was_successful():
            self.create_mixed_dataset_tree_view_items(task.result)
            self.create_mixed_dataset_stack_windows(task.result)
            self.view.model_changed.emit()
            task.result = None
        else:
            self._handle_task_error(self.LOAD_ERROR_STRING, log, task)

    def _on_dataset_load_done(self, task: 'TaskWorkerThread') -> None:
        log = getLogger(__name__)

        if task.was_successful():
            self._add_strict_dataset_to_view(task.result)
            self.view.model_changed.emit()
            task.result = None
        else:
            self._handle_task_error(self.LOAD_ERROR_STRING, log, task)

    def _add_strict_dataset_to_view(self, dataset: StrictDataset):
        """
        Takes a loaded dataset and tries to find a substitute 180 projection (if required) then creates the stack window
        and dataset tree view items.
        :param dataset: The loaded dataset.
        """
        self.create_strict_dataset_stack_windows(dataset)
        self.create_strict_dataset_tree_view_items(dataset)
        self.add_alternative_180_if_required(dataset)

    def _handle_task_error(self, base_message: str, log: Logger, task: 'TaskWorkerThread') -> None:
        msg = base_message.format(task.error)
        log.error(msg)
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

    def get_active_stack_visualisers(self) -> List[StackVisualiserView]:
        return [stack for stack in self.active_stacks.values()]

    def get_all_stacks(self) -> List[ImageStack]:
        return self.model.images

    def get_all_180_projections(self) -> List[ImageStack]:
        return self.model.proj180s

    def add_alternative_180_if_required(self, dataset: StrictDataset):
        """
        Checks if the dataset has a 180 projection and tries to find an alternative if one is missing.
        :param dataset: The loaded dataset.
        """
        if dataset.sample.has_proj180deg() and dataset.sample.proj180deg.filenames:  # type: ignore
            return
        else:
            closest_projection, diff = find_projection_closest_to_180(dataset.sample.projections,
                                                                      dataset.sample.projection_angles().value)
            if diff <= THRESHOLD_180 or self.view.ask_to_use_closest_to_180(diff):
                _180_arr = np.reshape(closest_projection, (1, ) + closest_projection.shape).copy()
                dataset.proj180deg = ImageStack(_180_arr, name=f"{dataset.name}_180")

                self.add_child_item_to_tree_view(dataset.id, dataset.proj180deg.id, "180")
                sample_vis = self.get_stack_visualiser(dataset.sample.id)
                self._create_and_tabify_stack_window(dataset.proj180deg, sample_vis)

    def create_strict_dataset_stack_windows(self, dataset: StrictDataset) -> StackVisualiserView:
        """
        Creates the stack widgets for the strict dataset.
        :param dataset: The loaded dataset.
        :return: The stack widget for the sample.
        """
        sample_stack_vis = self._create_lone_stack_window(dataset.sample)
        self._tabify_stack_window(sample_stack_vis)

        if dataset.flat_before and dataset.flat_before.filenames:
            self._create_and_tabify_stack_window(dataset.flat_before, sample_stack_vis)
        if dataset.flat_after and dataset.flat_after.filenames:
            self._create_and_tabify_stack_window(dataset.flat_after, sample_stack_vis)
        if dataset.dark_before and dataset.dark_before.filenames:
            self._create_and_tabify_stack_window(dataset.dark_before, sample_stack_vis)
        if dataset.dark_after and dataset.dark_after.filenames:
            self._create_and_tabify_stack_window(dataset.dark_after, sample_stack_vis)
        if dataset.sample.has_proj180deg() and dataset.sample.proj180deg.filenames:  # type: ignore
            self._create_and_tabify_stack_window(
                dataset.sample.proj180deg,  # type: ignore
                sample_stack_vis)

        self._focus_on_newest_stack_tab()
        return sample_stack_vis

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

    def create_mixed_dataset_stack_windows(self, dataset: MixedDataset) -> StackVisualiserView:
        """
        Creates stack windows for a mixed dataset.
        :param dataset: The dataset object.
        :return: The first stack visualiser from the dataset.
        """
        first_stack_vis = self._create_lone_stack_window(dataset.all[0])
        self._tabify_stack_window(first_stack_vis)

        for i in range(1, len(dataset.all)):
            self._create_and_tabify_stack_window(dataset.all[i], first_stack_vis)

        self._focus_on_newest_stack_tab()
        return first_stack_vis

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

    def _create_lone_stack_window(self, images: ImageStack):
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
                             tabify_stack: Optional[StackVisualiserView] = None):
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

    def create_strict_dataset_tree_view_items(self, dataset: StrictDataset):
        """
        Creates the tree view items for a strict dataset.
        :param dataset: The loaded dataset.
        """
        dataset_tree_item = self.view.create_dataset_tree_widget_item(dataset.name, dataset.id)
        self.view.create_child_tree_item(dataset_tree_item, dataset.sample.id, "Projections")

        if dataset.flat_before and dataset.flat_before.filenames:
            self.view.create_child_tree_item(dataset_tree_item, dataset.flat_before.id, "Flat Before")
        if dataset.flat_after and dataset.flat_after.filenames:
            self.view.create_child_tree_item(dataset_tree_item, dataset.flat_after.id, "Flat After")
        if dataset.dark_before and dataset.dark_before.filenames:
            self.view.create_child_tree_item(dataset_tree_item, dataset.dark_before.id, "Dark Before")
        if dataset.dark_after and dataset.dark_after.filenames:
            self.view.create_child_tree_item(dataset_tree_item, dataset.dark_after.id, "Dark After")
        if dataset.sample.has_proj180deg() and dataset.sample.proj180deg.filenames:  # type: ignore
            self.view.create_child_tree_item(
                dataset_tree_item,
                dataset.sample.proj180deg.id,  # type: ignore
                "180")

        self.view.add_item_to_tree_view(dataset_tree_item)

    def create_mixed_dataset_tree_view_items(self, dataset: MixedDataset):
        """
        Creates the tree view items for a mixed dataset.
        :param dataset: The loaded dataset.
        """
        dataset_tree_item = self.view.create_dataset_tree_widget_item(dataset.name, dataset.id)

        for i in range(len(dataset.all)):
            self.view.create_child_tree_item(dataset_tree_item, dataset.all[i].id, dataset.all[i].name)

        self.view.add_item_to_tree_view(dataset_tree_item)

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

    def _on_save_done(self, task: 'TaskWorkerThread') -> None:
        log = getLogger(__name__)

        if not task.was_successful():
            self._handle_task_error(self.SAVE_ERROR_STRING, log, task)

    @property
    def stack_visualiser_list(self) -> List[StackId]:
        stacks = [StackId(stack_id, widget.windowTitle()) for stack_id, widget in self.active_stacks.items()]
        return sorted(stacks, key=lambda x: x.name)

    @property
    def datasets(self) -> Iterable[Union[MixedDataset, StrictDataset]]:
        return self.model.datasets.values()

    @property
    def strict_dataset_list(self) -> List[DatasetId]:
        datasets = [
            DatasetId(dataset.id, dataset.name) for dataset in self.model.datasets.values()
            if isinstance(dataset, StrictDataset)
        ]
        return sorted(datasets, key=lambda x: x.name)

    @property
    def all_dataset_ids(self) -> Iterable[uuid.UUID]:
        return self.model.datasets.keys()

    @property
    def stack_visualiser_names(self) -> List[str]:
        return [widget.windowTitle() for widget in self.stack_visualisers.values()]

    def get_dataset(self, dataset_id: uuid.UUID) -> Optional[Union[MixedDataset, StrictDataset]]:
        return self.model.datasets.get(dataset_id)

    def get_stack_visualiser(self, stack_id: uuid.UUID) -> StackVisualiserView:
        return self.stack_visualisers[stack_id]

    def get_stack(self, stack_id: uuid.UUID) -> ImageStack:
        images = self.model.get_images_by_uuid(stack_id)
        if images is None:
            raise RuntimeError(f"Stack not found: {stack_id}")
        return images

    def get_stack_visualiser_history(self, stack_id: uuid.UUID) -> Dict[str, Any]:
        return self.get_stack_visualiser(stack_id).presenter.images.metadata

    def get_dataset_id_for_stack(self, stack_id: uuid.UUID) -> uuid.UUID:
        return self.model.get_parent_dataset(stack_id)

    @property
    def active_stacks(self) -> Dict[uuid.UUID, StackVisualiserView]:
        return {stack_id: stack for (stack_id, stack) in self.stack_visualisers.items() if stack.isVisible()}

    @property
    def have_active_stacks(self) -> bool:
        return len(self.active_stacks) > 0

    def get_stack_with_images(self, images: ImageStack) -> StackVisualiserView:
        for _, sv in self.stack_visualisers.items():
            if images is sv.presenter.images:
                return sv
        raise RuntimeError(f"Did not find stack {images} in stacks! " f"Stacks: {self.stack_visualisers.items()}")

    def add_180_deg_file_to_dataset(self, dataset_id: uuid.UUID, _180_deg_file: str):
        """
        Loads a 180 file then adds it to the dataset, creates a stack window, and updates the dataset tree view.
        :param dataset_id: The ID of the dataset to update.
        :param _180_deg_file: The filename for the 180 file.
        """
        existing_180_id = self.model.get_existing_180_id(dataset_id)
        _180_deg = self.model.add_180_deg_to_dataset(dataset_id, _180_deg_file)
        stack = self.create_single_tabbed_images_stack(_180_deg)
        stack.raise_()

        if existing_180_id is None:
            self.add_child_item_to_tree_view(dataset_id, _180_deg.id, "180")
        else:
            self.replace_child_item_id(dataset_id, existing_180_id, _180_deg.id)
            self._delete_stack(existing_180_id)

        self.view.model_changed.emit()

    def replace_child_item_id(self, dataset_id: uuid.UUID, prev_id: uuid.UUID, new_id: uuid.UUID):
        """
        Replaces the ID in an existing child item.
        :param dataset_id: The ID of the parent dataset.
        :param prev_id: The previous ID of the tree view item.
        :param new_id: The new ID that should be given to the tree view item.
        """
        dataset_item = self.view.get_dataset_tree_view_item(dataset_id)
        for i in range(dataset_item.childCount()):
            child = dataset_item.child(i)
            if child.id == prev_id:
                child._id = new_id
                return
        raise RuntimeError(f"Failed to get tree view item with ID {prev_id}")

    def add_projection_angles_to_sample(self, stack_id: uuid.UUID, proj_angles: ProjectionAngles) -> None:
        self.model.add_projection_angles_to_sample(stack_id, proj_angles)

    def load_stacks_from_folder(self, file_path: str) -> bool:
        loading_params = create_loading_parameters_for_file_path(file_path, logger)
        if loading_params is None:
            return False

        self.load_image_files(loading_params)
        return True

    def wizard_action_load(self) -> None:
        self.view.show_image_load_dialog()

    def show_operation(self, operation_name: str) -> None:
        self.view.show_filters_window()
        self.view.filters.presenter.set_filter_by_name(operation_name)  # type:ignore[union-attr]

    def wizard_action_show_reconstruction(self) -> None:
        self.view.show_recon_window()

    def remove_item_from_tree_view(self, uuid_remove: uuid.UUID) -> None:

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

    def add_child_item_to_tree_view(self, parent_id: uuid.UUID, child_id: uuid.UUID, child_name: str):
        """
        Adds a child item to the tree view.
        :param parent_id: The ID of the parent dataset.
        :param child_id: The ID of the corresponding ImageStack object.
        :param child_name: The name that should appear in the tree view.
        """
        dataset_item = self.view.get_dataset_tree_view_item(parent_id)
        self.view.create_child_tree_item(dataset_item, child_id, child_name)

    def add_recon_item_to_tree_view(self, parent_id: uuid.UUID, child_id: uuid.UUID, name: str):
        """
        Adds a recon item to the tree view.
        :param parent_id: The ID of the parent dataset.
        :param child_id: The ID of the corresponding ImageStack object.
        :param name: The name to display for the recon in the tree view.
        """
        dataset_item = self.view.get_dataset_tree_view_item(parent_id)

        recon_group = self.view.get_recon_group(dataset_item)
        if not recon_group:
            recon_group = self.view.add_recon_group(dataset_item, self.model.get_recon_list_id(parent_id))

        self.view.create_child_tree_item(recon_group, child_id, name)

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
                self._delete_stack(stack_id)

        # If the container_id provided is not a stack id then we remove the entire container from the tree view,
        # otherwise we remove the individual stacks that were deleted
        tree_view_items_to_remove = [container_id] if container_id not in removed_stack_ids else removed_stack_ids
        for item_id in tree_view_items_to_remove:
            self.remove_item_from_tree_view(item_id)

        self.view.model_changed.emit()

    def _delete_stack(self, stack_id: uuid.UUID) -> None:
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
        parent_id = self.model.add_recon_to_dataset(recon_data, stack_id)
        self.view.create_new_stack(recon_data)
        self.add_recon_item_to_tree_view(parent_id, recon_data.id, recon_data.name)
        self.view.model_changed.emit()

    def add_sinograms_to_dataset_and_update_view(self, sino_stack: ImageStack, original_stack_id: uuid.UUID):
        """
        Adds sinograms to a dataset or replaces an existing one.
        :param sino_stack: The sinogram stack.
        :param original_stack_id: The ID of a stack in the dataset.
        """
        parent_id = self.model.get_parent_dataset(original_stack_id)
        prev_sino = self.model.datasets[parent_id].sinograms
        if prev_sino is not None:
            self._delete_stack(prev_sino.id)
        self.model.datasets[parent_id].sinograms = sino_stack
        self._add_sinograms_to_tree_view(sino_stack.id, parent_id)
        self.create_single_tabbed_images_stack(sino_stack)
        self.view.model_changed.emit()

    def _add_sinograms_to_tree_view(self, sino_id: uuid.UUID, parent_id: uuid.UUID):
        """
        Adds a sinograms item to the tree view or updates the id of an existing one.
        :param parent_id: The ID of the parent dataset.
        :param sino_id: The ID of the corresponding ImageStack object.
        """
        dataset_item = self.view.get_dataset_tree_view_item(parent_id)
        sinograms_item = self.view.get_sinograms_item(dataset_item)
        if sinograms_item is None:
            self.view.create_child_tree_item(dataset_item, sino_id, self.view.sino_text)
        else:
            sinograms_item._id = sino_id

    def _show_add_stack_to_dataset_dialog(self, container_id: uuid.UUID):
        """
        Asks the user to add a stack to a given dataset.
        :param container_id: The ID of the dataset or stack.
        """
        if container_id not in self.all_dataset_ids:
            # get parent ID if selected item is a stack
            container_id = self.get_dataset_id_for_stack(container_id)
        self.view.show_add_stack_to_existing_dataset_dialog(container_id)

    def _add_images_to_existing_dataset(self):
        """
        Adds / replaces images to an existing dataset. Updates the tree view and deletes the previous stack if
        necessary.
        """
        assert self.view.add_to_dataset_dialog is not None

        dataset_id = self.view.add_to_dataset_dialog.dataset_id
        dataset = self.get_dataset(dataset_id)
        new_images = self.view.add_to_dataset_dialog.presenter.images
        images_text = self.view.add_to_dataset_dialog.images_type
        image_attr = images_text.replace(" ", "_").lower()

        if getattr(dataset, image_attr) is None:
            self.add_child_item_to_tree_view(dataset_id, new_images.id, images_text)

        else:
            prev_images_id = getattr(dataset, image_attr).id
            self.replace_child_item_id(dataset_id, prev_images_id, new_images.id)
            self._delete_stack(prev_images_id)

        setattr(dataset, image_attr, new_images)
        self.create_single_tabbed_images_stack(new_images)
        self.view.model_changed.emit()

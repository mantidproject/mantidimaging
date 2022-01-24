# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import traceback
import uuid
from enum import Enum, auto
from logging import getLogger, Logger
from typing import TYPE_CHECKING, Optional, Dict, List, Any, NamedTuple

import numpy as np
from PyQt5.QtWidgets import QTabBar, QApplication

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import StrictDataset, MixedDataset
from mantidimaging.core.io.loader.loader import create_loading_parameters_for_file_path
from mantidimaging.core.io.utility import find_projection_closest_to_180, THRESHOLD_180
from mantidimaging.core.utility.data_containers import ProjectionAngles, LoadingParameters
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.stack_visualiser.presenter import SVNotification
from mantidimaging.gui.windows.stack_visualiser.view import StackVisualiserView
from .model import MainWindowModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.save_dialog import MWSaveDialog
    from mantidimaging.gui.dialogs.async_task.task import TaskWorkerThread


class StackId(NamedTuple):
    id: uuid.UUID
    name: str


class DatasetId(NamedTuple):
    id: uuid.UUID
    name: str


logger = getLogger(__name__)


class Notification(Enum):
    LOAD = auto()
    SAVE = auto()
    REMOVE_STACK = auto()
    RENAME_STACK = auto()
    NEXUS_LOAD = auto()
    FOCUS_TAB = auto()
    ADD_RECON = auto()


class MainWindowPresenter(BasePresenter):
    LOAD_ERROR_STRING = "Failed to load stack. Error: {}"
    SAVE_ERROR_STRING = "Failed to save stack. Error: {}"

    view: 'MainWindowView'

    def __init__(self, view: 'MainWindowView'):
        super().__init__(view)
        self.model = MainWindowModel()
        self.stacks: Dict[uuid.UUID, StackVisualiserView] = {}

    def notify(self, signal: Notification, **baggage):
        try:
            if signal == Notification.LOAD:
                self.load_dataset()
            elif signal == Notification.SAVE:
                self.save()
            elif signal == Notification.REMOVE_STACK:
                self._delete_container(**baggage)
            elif signal == Notification.RENAME_STACK:
                self._do_rename_stack(**baggage)
            elif signal == Notification.NEXUS_LOAD:
                self.load_nexus_file()
            elif signal == Notification.FOCUS_TAB:
                self._focus_tab(**baggage)
            elif signal == Notification.ADD_RECON:
                self._add_recon_to_dataset(**baggage)

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def _get_stack_widget_by_name(self, search_name: str) -> Optional[StackVisualiserView]:
        """
        Uses the stack name to retrieve the QDockWidget object.
        :param search_name: The name of the stack widget to find.
        :return: The QDockWidget if it could be found, None otherwise.
        """
        for stack_id in self.stack_list:
            if stack_id.name == search_name:
                return self.active_stacks[stack_id.id]
        return None

    def get_stack_id_by_name(self, search_name: str) -> Optional[uuid.UUID]:
        for stack_id in self.stack_list:
            if stack_id.name == search_name:
                return stack_id.id
        return None

    def add_log_to_sample(self, stack_name: str, log_file: str) -> None:
        stack_id = self.get_stack_id_by_name(stack_name)
        if stack_id is None:
            raise RuntimeError(f"Failed to get stack with name {stack_name}")
        self.model.add_log_to_sample(stack_id, log_file)

    def _do_rename_stack(self, current_name: str, new_name: str) -> None:
        dock = self._get_stack_widget_by_name(current_name)
        if dock is not None:
            dock.setWindowTitle(new_name)
            self.view.model_changed.emit()

    def load_dataset(self, par: Optional[LoadingParameters] = None) -> None:
        if par is None and self.view.load_dialogue is not None:
            par = self.view.load_dialogue.get_parameters()
        if par is None:
            return

        if par.sample.input_path == "":
            raise ValueError("No sample path provided")

        start_async_task_view(self.view, self.model.do_load_dataset, self._on_dataset_load_done, {'parameters': par})

    def load_nexus_file(self) -> None:
        assert self.view.nexus_load_dialog is not None
        dataset, _ = self.view.nexus_load_dialog.presenter.get_dataset()
        self.model.add_dataset_to_model(dataset)
        self._add_strict_dataset_to_view(dataset)
        self.view.model_changed.emit()

    def load_image_stack(self, file_path: str) -> None:
        start_async_task_view(self.view, self.model.load_images, self._on_stack_load_done, {'file_path': file_path})

    def _on_stack_load_done(self, task: 'TaskWorkerThread') -> None:
        log = getLogger(__name__)

        if task.was_successful():
            task.result.name = os.path.splitext(task.kwargs['file_path'])[0]
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
        self.check_dataset_180(dataset)
        self.create_strict_dataset_stack_windows(dataset)
        self.create_dataset_tree_view_items(dataset)

    def _handle_task_error(self, base_message: str, log: Logger, task: 'TaskWorkerThread') -> None:
        msg = base_message.format(task.error)
        log.error(msg)
        self.show_error(msg, traceback.format_exc())

    def _create_and_tabify_stack_window(self, images: Images, sample_dock: StackVisualiserView) -> None:
        """
        Creates a new stack window with a given Images object then makes sure it is placed on top of a sample/original
        stack window.
        :param images: The Images object for the new stack window.
        :param sample_dock: The existing stack window that the new one should be placed on top of.
        """
        stack_visualiser = self._create_lone_stack_window(images)
        self.view.tabifyDockWidget(sample_dock, stack_visualiser)

    def get_active_stack_visualisers(self) -> List[StackVisualiserView]:
        return [stack for stack in self.active_stacks.values()]

    def create_new_180_stack(self, container: Images) -> StackVisualiserView:
        _180_stack_vis = self.view.create_stack_window(container)

        current_stack_visualisers = self.get_active_stack_visualisers()
        if len(current_stack_visualisers) > 1:
            self.view.tabifyDockWidget(current_stack_visualisers[0], _180_stack_vis)

            tab_bar = self.view.findChild(QTabBar)
            if tab_bar is not None:
                last_stack_pos = len(current_stack_visualisers)
                # make Qt process the addition of the dock onto the main window
                QApplication.sendPostedEvents()
                tab_bar.setCurrentIndex(last_stack_pos)

        return _180_stack_vis

    def check_dataset_180(self, dataset: StrictDataset):
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
                dataset.proj180deg = Images(np.reshape(closest_projection, (1, ) + closest_projection.shape),
                                            name=f"{dataset.name}_180")

    def create_strict_dataset_stack_windows(self, dataset: StrictDataset) -> StackVisualiserView:
        """
        Creates the stack widgets for the strict dataset.
        :param dataset: The loaded dataset.
        :return: The stack widget for the sample.
        """
        sample_stack_vis = self._create_lone_stack_window(dataset.sample)

        current_stack_visualisers = self.get_active_stack_visualisers()
        if len(current_stack_visualisers) > 0:
            self.view.tabifyDockWidget(current_stack_visualisers[0], sample_stack_vis)

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

        self._focus_on_newest_stack_window()
        return sample_stack_vis

    def _focus_on_newest_stack_window(self) -> None:
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
        first_stack_vis = self._create_lone_stack_window(dataset.all[0])

        current_stack_visualisers = self.get_active_stack_visualisers()
        if len(current_stack_visualisers) > 0:
            self.view.tabifyDockWidget(current_stack_visualisers[0], first_stack_vis)

        for i in range(1, len(dataset.all)):
            self._create_and_tabify_stack_window(dataset.all[i], first_stack_vis)

        self._focus_on_newest_stack_window()
        return first_stack_vis

    def create_single_images_stack(self, images: Images) -> StackVisualiserView:
        """
        Creates a stack for a single Images object and focuses on it.
        :param images: The Images object for the new stack window.
        :return: The new StackVisualiserView.
        """
        stack_vis = self._create_lone_stack_window(images)

        current_stack_visualisers = self.get_active_stack_visualisers()
        if len(current_stack_visualisers) > 0:
            self.view.tabifyDockWidget(current_stack_visualisers[0], stack_vis)

        self._focus_on_newest_stack_window()
        return stack_vis

    def _create_lone_stack_window(self, images: Images):
        """
        Creates a stack window and adds it to the stack list without tabifying.
        :param images: The Images array for the stack window to display.
        :return: The new stack window.
        """
        stack_vis = self.view.create_stack_window(images)
        self.stacks[stack_vis.id] = stack_vis
        return stack_vis

    def create_dataset_tree_view_items(self, dataset: StrictDataset):
        """
        Creates the dataset tree view items for a dataset.
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

    def save(self) -> None:
        assert isinstance(self.view.save_dialogue, MWSaveDialog)
        kwargs = {
            'images_id': self.view.save_dialogue.selected_stack,
            'output_dir': self.view.save_dialogue.save_path(),
            'name_prefix': self.view.save_dialogue.name_prefix(),
            'image_format': self.view.save_dialogue.image_format(),
            'overwrite': self.view.save_dialogue.overwrite(),
            'pixel_depth': self.view.save_dialogue.pixel_depth()
        }
        start_async_task_view(self.view, self.model.do_images_saving, self._on_save_done, kwargs)

    def _on_save_done(self, task: 'TaskWorkerThread') -> None:
        log = getLogger(__name__)

        if not task.was_successful():
            self._handle_task_error(self.SAVE_ERROR_STRING, log, task)

    @property
    def stack_list(self) -> List[StackId]:  # todo: rename?
        stacks = [StackId(stack_id, widget.windowTitle()) for stack_id, widget in self.active_stacks.items()]
        return sorted(stacks, key=lambda x: x.name)

    @property
    def dataset_list(self) -> List[DatasetId]:
        datasets = [
            DatasetId(dataset.id, dataset.name) for dataset in self.model.datasets.values()
            if isinstance(dataset, StrictDataset)
        ]
        return sorted(datasets, key=lambda x: x.name)

    @property
    def stack_names(self) -> List[str]:
        return [widget.windowTitle() for widget in self.stacks.values()]

    def get_stack_visualiser(self, stack_id: uuid.UUID) -> StackVisualiserView:
        return self.active_stacks[stack_id]

    def get_stack_history(self, stack_id: uuid.UUID) -> Dict[str, Any]:
        return self.get_stack_visualiser(stack_id).presenter.images.metadata

    @property
    def active_stacks(self) -> Dict[uuid.UUID, StackVisualiserView]:
        return {stack_id: stack for (stack_id, stack) in self.stacks.items() if stack.isVisible()}

    def get_all_stack_visualisers_with_180deg_proj(self) -> List[StackVisualiserView]:
        return [stack for stack in self.stacks.values() if stack.presenter.images.has_proj180deg()]

    @property
    def have_active_stacks(self) -> bool:
        return len(self.active_stacks) > 0

    def update_stack_with_images(self, images: Images) -> None:
        sv = self.get_stack_with_images(images)
        if sv is not None:
            sv.presenter.notify(SVNotification.REFRESH_IMAGE)

    def get_stack_with_images(self, images: Images) -> StackVisualiserView:
        for _, sv in self.stacks.items():
            if images is sv.presenter.images:
                return sv
        raise RuntimeError(f"Did not find stack {images} in stacks! " f"Stacks: {self.stacks.items()}")

    def set_images_in_stack(self, stack_id: uuid.UUID, images: Images) -> None:
        self.model.set_image_data_by_uuid(stack_id, images.data)
        stack = self.stacks[stack_id]
        if not stack.presenter.images == images:  # todo - refactor
            stack.image_view.clear()
            stack.image_view.setImage(images.data)

            # Free previous images stack before reassignment
            stack.presenter.images.data = images.data

    def add_180_deg_to_dataset(self, dataset_id: uuid.UUID,
                               _180_deg_file: str) -> Optional[Images]:  # todo - break method
        _180_deg = self.model.add_180_deg_to_dataset(dataset_id, _180_deg_file)
        if not isinstance(_180_deg, Images):
            return None
        self.view.model_changed.emit()
        return _180_deg

    def add_projection_angles_to_sample(self, stack_name: str, proj_angles: ProjectionAngles) -> None:
        stack_id = self.get_stack_id_by_name(stack_name)
        if stack_id is None:
            raise RuntimeError(f"Failed to get stack with name {stack_name}")
        self.model.add_projection_angles_to_sample(stack_id, proj_angles)

    def load_stacks_from_folder(self, file_path: str) -> bool:
        loading_params = create_loading_parameters_for_file_path(file_path, logger)
        if loading_params is None:
            return False

        self.load_dataset(loading_params)
        return True

    def wizard_action_load(self) -> None:
        self.view.show_load_dialogue()

    def show_operation(self, operation_name: str) -> None:
        self.view.show_filters_window()
        self.view.filters.presenter.set_filter_by_name(operation_name)  # type:ignore[union-attr]

    def wizard_action_show_reconstruction(self) -> None:
        self.view.show_recon_window()

    def remove_item_from_tree_view(self, uuid_remove: uuid.UUID) -> None:
        top_level_item_count = self.view.dataset_tree_widget.topLevelItemCount()

        for i in range(top_level_item_count):
            top_level_item = self.view.dataset_tree_widget.topLevelItem(i)
            if top_level_item.id == uuid_remove:
                self.view.dataset_tree_widget.takeTopLevelItem(i)
                return

            child_count = top_level_item.childCount()
            for j in range(child_count):
                child_item = top_level_item.child(j)
                if child_item.id == uuid_remove:
                    top_level_item.takeChild(j)
                    return

    def add_child_item_to_tree_view(self, parent_id: uuid.UUID, child_id: uuid.UUID, child_name: str):
        top_level_item_count = self.view.dataset_tree_widget.topLevelItemCount()
        for i in range(top_level_item_count):
            top_level_item = self.view.dataset_tree_widget.topLevelItem(i)
            if top_level_item.id == parent_id:
                self.view.create_child_tree_item(top_level_item, child_id, child_name)
                return
        raise RuntimeError(f"Unable to add 180 item to dataset tree item with ID {parent_id}")

    def add_stack_to_dictionary(self, stack: StackVisualiserView) -> None:
        self.stacks[stack.id] = stack

    def _delete_container(self, container_id: uuid.UUID) -> None:
        """
        Informs the model to delete a container, then updates the view elements.
        :param container_id: The ID of the container to delete.
        """
        ids_to_remove = self.model.remove_container(container_id)
        if ids_to_remove is None:
            return
        if len(ids_to_remove) == 1:
            self._delete_stack(container_id)
        else:
            for stack_id in ids_to_remove:
                self._delete_stack(stack_id)
        self.remove_item_from_tree_view(container_id)
        self.view.model_changed.emit()

    def _delete_stack(self, stack_id: uuid.UUID) -> None:
        """
        Deletes a stack and frees memory.
        :param stack_id: The ID of the stack to delete.
        """
        self.stacks[stack_id].image_view.close()
        self.stacks[stack_id].presenter.delete_data()
        self.stacks[stack_id].deleteLater()
        del self.stacks[stack_id]

    def _focus_tab(self, stack_id: uuid.UUID) -> None:
        """
        Makes a stack tab visible and brings it to the front. If dataset ID is given then nothing happens.
        :param stack_id: The ID of the stack tab to focus on.
        """
        if stack_id in self.model.datasets:
            return
        if stack_id in self.model.image_ids:
            self.stacks[stack_id].setVisible(True)
            self.stacks[stack_id].raise_()
        else:
            raise RuntimeError(f"Unable to find stack with ID {stack_id}")

    def _add_recon_to_dataset(self, recon_data: Images, stack_id: uuid.UUID) -> None:
        self.model.add_recon_to_dataset(recon_data, stack_id)

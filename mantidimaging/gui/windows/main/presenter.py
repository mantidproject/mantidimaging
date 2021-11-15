# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import traceback
import uuid
from collections import namedtuple
from enum import Enum, auto
from logging import getLogger
from typing import TYPE_CHECKING, Union, Optional, Dict, List, Any
from uuid import UUID

import numpy as np
from PyQt5.QtWidgets import QTabBar, QApplication, QDockWidget

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
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

StackId = namedtuple('StackId', ['id', 'name'])
logger = getLogger(__name__)


class Notification(Enum):
    LOAD = auto()
    SAVE = auto()
    REMOVE_STACK = auto()
    RENAME_STACK = auto()
    NEXUS_LOAD = auto()
    DATASET_DELETE = auto()
    IMAGES_DELETE = auto()


class MainWindowPresenter(BasePresenter):
    LOAD_ERROR_STRING = "Failed to load stack. Error: {}"
    SAVE_ERROR_STRING = "Failed to save stack. Error: {}"

    view: 'MainWindowView'

    def __init__(self, view):
        super(MainWindowPresenter, self).__init__(view)
        self.model = MainWindowModel()
        self.stacks: Dict[uuid.UUID, StackVisualiserView] = {}

    def notify(self, signal, **baggage):
        try:
            if signal == Notification.LOAD:
                self.load_dataset()
            elif signal == Notification.SAVE:
                self.save()
            elif signal == Notification.REMOVE_STACK:
                self._do_remove_stack(**baggage)
            elif signal == Notification.RENAME_STACK:
                self._do_rename_stack(**baggage)
            elif signal == Notification.NEXUS_LOAD:
                self.load_nexus_file()
            elif signal == Notification.IMAGES_DELETE:
                pass
            elif signal == Notification.DATASET_DELETE:
                pass

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def _get_stack_widget_by_name(self, search_name: str) -> Optional[QDockWidget]:
        """
        Uses the stack name to retrieve the QDockWidget object.
        :param search_name: The name of the stack widget to find.
        :return: The QDockWidget if it could be found, None otherwise.
        """
        for stack_id in self.stack_list:
            if stack_id.name == search_name:
                return self.active_stacks[stack_id.id]  # type:ignore
        return None

    def get_stack_id_by_name(self, search_name: str) -> Optional[uuid.UUID]:
        for stack_id in self.stack_list:
            if stack_id.name == search_name:
                return stack_id.id
        return None

    def add_log_to_sample(self, stack_name: str, log_file: str):
        stack_id = self.get_stack_id_by_name(stack_name)
        if stack_id is None:
            raise RuntimeError(f"Failed to get stack with name {stack_name}")
        self.model.add_log_to_sample(stack_id, log_file)

    def _do_remove_stack(self, stack_uuid: UUID):
        self.remove_item_from_tree_view(stack_uuid)
        self.model.remove_container(stack_uuid)
        del self.stacks[stack_uuid]
        self.view.active_stacks_changed.emit()  # TODO: change to stacks changed?

    def _do_rename_stack(self, current_name: str, new_name: str):
        dock = self._get_stack_widget_by_name(current_name)
        if dock:
            dock.setWindowTitle(new_name)
            self.view.active_stacks_changed.emit()

    def load_dataset(self, par: Optional[LoadingParameters] = None):
        if par is None and self.view.load_dialogue is not None:
            par = self.view.load_dialogue.get_parameters()
        if par is None:
            return

        if par.sample.input_path == "":
            raise ValueError("No sample path provided")

        start_async_task_view(self.view, self.model.do_load_dataset, self._on_dataset_load_done, {'parameters': par})

    def load_nexus_file(self):
        loading_dataset, title = self.view.nexus_load_dialog.presenter.get_dataset()
        self.create_new_stack(self.model.convert_loading_dataset(loading_dataset), title)

    def load_image_stack(self, file_path: str):
        start_async_task_view(self.view, self.model.load_images, self._on_stack_load_done, {'file_path': file_path})

    def _on_stack_load_done(self, task):
        log = getLogger(__name__)

        if task.was_successful():
            self.create_new_stack(task.result, self.create_stack_name(task.kwargs['file_path']))
            task.result = None
        else:
            self._handle_task_error(self.LOAD_ERROR_STRING, log, task)

    def _on_dataset_load_done(self, task):
        log = getLogger(__name__)

        if task.was_successful():
            title = task.kwargs['parameters'].name
            self.create_new_stack(task.result, title)
            task.result = None
        else:
            self._handle_task_error(self.LOAD_ERROR_STRING, log, task)

    def _handle_task_error(self, base_message: str, log, task):
        msg = base_message.format(task.error)
        log.error(msg)
        self.show_error(msg, traceback.format_exc())

    def _add_stack(self, images: Images, filename: str, sample_dock):
        name = self.create_stack_name(os.path.basename(filename))
        stack_visualiser = self.view.create_stack_window(images, title=f"{name}")
        self.view.tabifyDockWidget(sample_dock, stack_visualiser)
        self.stacks[stack_visualiser.uuid] = stack_visualiser

    def get_active_stack_visualisers(self) -> List[StackVisualiserView]:
        return [stack for stack in self.active_stacks.values()]  # type:ignore

    def create_new_180_stack(self, container: Images, title: str):
        title = self.create_stack_name(title)
        _180_stack_vis = self.view.create_stack_window(container, title)

        current_stack_visualisers = self.get_active_stack_visualisers()
        if len(current_stack_visualisers) > 1:
            self.view.tabifyDockWidget(current_stack_visualisers[0], _180_stack_vis)

            tab_bar = self.view.findChild(QTabBar)
            if tab_bar is not None:
                last_stack_pos = len(current_stack_visualisers) - 1
                # make Qt process the addition of the dock onto the main window
                QApplication.sendPostedEvents()
                tab_bar.setCurrentIndex(last_stack_pos)

        self.view.active_stacks_changed.emit()

        return _180_stack_vis

    def create_new_stack(self, container: Union[Images, Dataset], title: str):
        title = self.create_stack_name(title)

        sample = container if isinstance(container, Images) else container.sample
        sample_stack_vis = self.view.create_stack_window(sample, title)
        self.stacks[sample_stack_vis.uuid] = sample_stack_vis

        current_stack_visualisers = self.get_active_stack_visualisers()
        if len(current_stack_visualisers) > 0:
            self.view.tabifyDockWidget(current_stack_visualisers[0], sample_stack_vis)

        dataset_tree_item = self.view.create_dataset_tree_widget_item(title, sample_stack_vis.uuid)

        if isinstance(container, Dataset):
            self.view.create_child_tree_item(dataset_tree_item, container.sample.id, "Projections")
            if container.flat_before and container.flat_before.filenames:
                self._add_stack(container.flat_before, container.flat_before.filenames[0], sample_stack_vis)
                self.view.create_child_tree_item(dataset_tree_item, container.flat_before.id, "Flat Before")
            if container.flat_after and container.flat_after.filenames:
                self._add_stack(container.flat_after, container.flat_after.filenames[0], sample_stack_vis)
                self.view.create_child_tree_item(dataset_tree_item, container.flat_after.id, "Flat After")
            if container.dark_before and container.dark_before.filenames:
                self._add_stack(container.dark_before, container.dark_before.filenames[0], sample_stack_vis)
                self.view.create_child_tree_item(dataset_tree_item, container.dark_before.id, "Dark Before")
            if container.dark_after and container.dark_after.filenames:
                self._add_stack(container.dark_after, container.dark_after.filenames[0], sample_stack_vis)
                self.view.create_child_tree_item(dataset_tree_item, container.dark_after.id, "Dark After")
            if container.sample.has_proj180deg() and container.sample.proj180deg.filenames:  # type: ignore
                self._add_stack(
                    container.sample.proj180deg,  # type: ignore
                    container.sample.proj180deg.filenames[0],  # type: ignore
                    sample_stack_vis)
                self.view.create_child_tree_item(
                    dataset_tree_item,
                    container.sample.proj180deg.id,  # type: ignore
                    "180")
            else:
                closest_projection, diff = find_projection_closest_to_180(sample.projections,
                                                                          sample.projection_angles().value)
                if diff <= THRESHOLD_180 or self.view.ask_to_use_closest_to_180(diff):
                    container.sample.proj180deg = Images(
                        np.reshape(closest_projection, (1, ) + closest_projection.shape))
                    self._add_stack(container.sample.proj180deg, f"{title}_180", sample_stack_vis)
                    self.view.create_child_tree_item(dataset_tree_item, container.sample.proj180deg.id, "180")

        if len(current_stack_visualisers) > 1:
            tab_bar = self.view.findChild(QTabBar)
            if tab_bar is not None:
                last_stack_pos = len(current_stack_visualisers) - 1
                # make Qt process the addition of the dock onto the main window
                QApplication.sendPostedEvents()
                tab_bar.setCurrentIndex(last_stack_pos)

        self.view.active_stacks_changed.emit()
        self.view.add_item_to_tree_view(dataset_tree_item)

        return sample_stack_vis

    def save(self):
        kwargs = {
            'stack_uuid': self.view.save_dialogue.selected_stack,
            'output_dir': self.view.save_dialogue.save_path(),
            'name_prefix': self.view.save_dialogue.name_prefix(),
            'image_format': self.view.save_dialogue.image_format(),
            'overwrite': self.view.save_dialogue.overwrite(),
            'pixel_depth': self.view.save_dialogue.pixel_depth()
        }
        start_async_task_view(self.view, self.model.do_images_saving, self._on_save_done, kwargs)

    def _on_save_done(self, task):
        log = getLogger(__name__)

        if not task.was_successful():
            self._handle_task_error(self.SAVE_ERROR_STRING, log, task)

    @property
    def stack_list(self):  # todo: rename?
        stacks = [StackId(stack_id, widget.windowTitle()) for stack_id, widget in self.active_stacks.items()]
        return sorted(stacks, key=lambda x: x.name)

    @property
    def stack_names(self):
        return [widget.windowTitle() for widget in self.stacks.values()]

    def get_stack_visualiser(self, stack_uuid: UUID) -> StackVisualiserView:
        return self.active_stacks[stack_uuid]

    def get_stack_history(self, stack_uuid: uuid.UUID) -> Dict[str, Any]:
        return self.get_stack_visualiser(stack_uuid).presenter.images.metadata

    @property
    def active_stacks(self):
        return {stack_id: stack for (stack_id, stack) in self.stacks.items() if stack.isVisible()}

    def get_all_stack_visualisers_with_180deg_proj(self):
        return [
            stack for stack in self.stacks.values()  # type:ignore
            if stack.presenter.images.has_proj180deg()
        ]

    @property
    def have_active_stacks(self):
        return len(self.active_stacks) > 0

    def update_stack_with_images(self, images: Images):
        sv = self.get_stack_with_images(images)
        if sv is not None:
            sv.presenter.notify(SVNotification.REFRESH_IMAGE)

    def get_stack_with_images(self, images: Images) -> StackVisualiserView:
        for _, sv in self.stacks.items():
            if images is sv.presenter.images:
                return sv
        raise RuntimeError(f"Did not find stack {images} in stacks! " f"Stacks: {self.stacks.items()}")

    def set_images_in_stack(self, uuid: UUID, images: Images):
        self.model.set_image_data_by_uuid(uuid, images.data)
        stack = self.stacks[uuid]
        if not stack.presenter.images == images:  # todo - refactor
            stack.image_view.clear()
            stack.image_view.setImage(images.data)

            # Free previous images stack before reassignment
            stack.presenter.images.data = images.data

    def add_180_deg_to_dataset(self, stack_name: str, _180_deg_file: str):
        stack_id = self.get_stack_id_by_name(stack_name)
        if stack_id is None:
            raise RuntimeError(f"Failed to get stack with name {stack_name}")
        return self.model.add_180_deg_to_dataset(stack_id, _180_deg_file)  # todo: assumes the stack is the sample?

    def create_stack_name(self, filename: str) -> str:
        """
        Creates a suitable name for a newly loaded stack.
        """
        # Avoid file extensions in names
        filename = os.path.splitext(filename)[0]

        # Avoid duplicate names
        name = filename
        num = 1
        while name in self.stack_names:
            num += 1
            name = f"{filename}_{num}"

        return name

    def add_projection_angles_to_sample(self, stack_name: str, proj_angles: ProjectionAngles):
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

    def wizard_action_load(self):
        self.view.show_load_dialogue()

    def show_operation(self, operation_name: str):
        self.view.show_filters_window()
        self.view.filters.presenter.set_filter_by_name(operation_name)  # type:ignore[union-attr]

    def wizard_action_show_reconstruction(self):
        self.view.show_recon_window()

    def remove_item_from_tree_view(self, uuid_remove: UUID):
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

    def add_stack_to_dictionary(self, stack: StackVisualiserView):
        self.stacks[stack.uuid] = stack

    def delete_container(self, container_id):
        ids_to_remove = self.model.remove_container(container_id)
        if len(ids_to_remove) == 1:
            self.stacks[container_id].deleteLater()
            del self.stacks[container_id]
            self.remove_item_from_tree_view(container_id)
        if len(ids_to_remove) > 1:
            for stack_id in ids_to_remove:
                self.stacks[stack_id].deleteLater()
                del self.stacks[stack_id]
            # self.remove_item_from_tree_view(container_id)

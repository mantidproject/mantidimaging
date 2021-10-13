# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import traceback
from enum import Enum, auto
from logging import getLogger
from typing import TYPE_CHECKING, Union, Optional
from uuid import UUID

import numpy as np
from PyQt5.QtWidgets import QTabBar, QApplication, QTreeWidgetItem

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

logger = getLogger(__name__)


class Notification(Enum):
    LOAD = auto()
    SAVE = auto()
    REMOVE_STACK = auto()
    RENAME_STACK = auto()
    NEXUS_LOAD = auto()


def _create_child_tree_item(parent: QTreeWidgetItem, name: str):
    child = QTreeWidgetItem(parent)
    child.setText(0, name)
    parent.addChild(child)


class MainWindowPresenter(BasePresenter):
    LOAD_ERROR_STRING = "Failed to load stack. Error: {}"
    SAVE_ERROR_STRING = "Failed to save stack. Error: {}"

    view: 'MainWindowView'

    def __init__(self, view):
        super(MainWindowPresenter, self).__init__(view)
        self.model = MainWindowModel()

    def notify(self, signal, **baggage):
        try:
            if signal == Notification.LOAD:
                self.load_dataset()
            elif signal == Notification.SAVE:
                self.save()
            elif signal == Notification.REMOVE_STACK:
                self._do_remove_stack(**baggage)
            elif signal == Notification.RENAME_STACK:
                self._do_rename(**baggage)
            elif signal == Notification.NEXUS_LOAD:
                self.load_nexus_file()

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def _do_remove_stack(self, uuid: UUID):
        self.model.do_remove_stack(uuid)
        self.view.active_stacks_changed.emit()

    def _do_rename(self, current_name: str, new_name: str):
        dock = self.model.get_stack_by_name(current_name)
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

        start_async_task_view(self.view, self.model.do_load_stack, self._on_dataset_load_done, {'parameters': par})

    def load_nexus_file(self):
        dataset, title = self.view.nexus_load_dialog.presenter.get_dataset()
        self.create_new_stack(dataset, title)

    def load_image_stack(self, file_path: str):
        start_async_task_view(self.view, self.model.load_stack, self._on_stack_load_done, {'file_path': file_path})

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
        name = self.model.create_name(os.path.basename(filename))
        stack_visualiser = self.view.create_stack_window(images, title=f"{name}")
        self.model.add_stack(stack_visualiser)
        self.view.tabifyDockWidget(sample_dock, stack_visualiser)

    def create_new_180_stack(self, container: Images, title: str):
        title = self.model.create_name(title)
        _180_stack_vis = self.view.create_stack_window(container, title)
        self.model.add_stack(_180_stack_vis)

        current_stack_visualisers = self.get_all_stack_visualisers()
        if len(current_stack_visualisers) > 1:
            self.view.tabifyDockWidget(current_stack_visualisers[0], _180_stack_vis)

        if len(current_stack_visualisers) > 1:
            tab_bar = self.view.findChild(QTabBar)
            if tab_bar is not None:
                last_stack_pos = len(current_stack_visualisers) - 1
                # make Qt process the addition of the dock onto the main window
                QApplication.sendPostedEvents()
                tab_bar.setCurrentIndex(last_stack_pos)

        self.view.active_stacks_changed.emit()

        return _180_stack_vis

    def create_new_stack(self, container: Union[Images, Dataset], title: str):
        title = self.model.create_name(title)

        sample = container if isinstance(container, Images) else container.sample
        sample_stack_vis = self.view.create_stack_window(sample, title)
        self.model.add_stack(sample_stack_vis)

        current_stack_visualisers = self.get_all_stack_visualisers()
        if len(current_stack_visualisers) > 1:
            self.view.tabifyDockWidget(current_stack_visualisers[0], sample_stack_vis)

        dataset_tree_item = QTreeWidgetItem(self.view.dataset_tree_widget)
        dataset_tree_item.setText(0, title)

        if isinstance(container, Dataset):
            if container.flat_before and container.flat_before.filenames:
                self._add_stack(container.flat_before, container.flat_before.filenames[0], sample_stack_vis)
                _create_child_tree_item(dataset_tree_item, "Flat Before")
            if container.flat_after and container.flat_after.filenames:
                self._add_stack(container.flat_after, container.flat_after.filenames[0], sample_stack_vis)
                _create_child_tree_item(dataset_tree_item, "Flat After")
            if container.dark_before and container.dark_before.filenames:
                self._add_stack(container.dark_before, container.dark_before.filenames[0], sample_stack_vis)
                _create_child_tree_item(dataset_tree_item, "Dark Before")
            if container.dark_after and container.dark_after.filenames:
                self._add_stack(container.dark_after, container.dark_after.filenames[0], sample_stack_vis)
                _create_child_tree_item(dataset_tree_item, "Dark After")
            if container.sample.has_proj180deg() and container.sample.proj180deg.filenames:  # type: ignore
                self._add_stack(
                    container.sample.proj180deg,  # type: ignore
                    container.sample.proj180deg.filenames[0],  # type: ignore
                    sample_stack_vis)
                _create_child_tree_item(dataset_tree_item, "180")
            else:
                closest_projection, diff = find_projection_closest_to_180(sample.projections,
                                                                          sample.projection_angles().value)
                if diff <= THRESHOLD_180 or self.view.ask_to_use_closest_to_180(diff):
                    container.sample.proj180deg = Images(
                        np.reshape(closest_projection, (1, ) + closest_projection.shape))
                    self._add_stack(container.sample.proj180deg, "180", sample_stack_vis)
                    _create_child_tree_item(dataset_tree_item, "180")

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
        start_async_task_view(self.view, self.model.do_saving, self._on_save_done, kwargs)

    def _on_save_done(self, task):
        log = getLogger(__name__)

        if not task.was_successful():
            self._handle_task_error(self.SAVE_ERROR_STRING, log, task)

    @property
    def stack_list(self):
        return self.model.stack_list

    @property
    def stack_names(self):
        return self.model._stack_names

    def get_stack_visualiser(self, stack_uuid: UUID) -> StackVisualiserView:
        return self.model.get_stack_visualiser(stack_uuid)

    def get_all_stack_visualisers(self):
        return self.model.get_all_stack_visualisers()

    def get_all_stack_visualisers_with_180deg_proj(self):
        return self.model.get_all_stack_visualisers_with_180deg_proj()

    def get_stack_history(self, stack_uuid: UUID):
        return self.model.get_stack_history(stack_uuid)

    @property
    def have_active_stacks(self):
        return self.model.have_active_stacks

    def update_stack_with_images(self, images: Images):
        sv = self.get_stack_with_images(images)
        if sv is not None:
            sv.presenter.notify(SVNotification.REFRESH_IMAGE)

    def get_stack_with_images(self, images: Images) -> StackVisualiserView:
        return self.model.get_stack_by_images(images)

    def add_log_to_sample(self, stack_name: str, log_file: str):
        self.model.add_log_to_sample(stack_name, log_file)

    def set_images_in_stack(self, uuid: UUID, images: Images):
        self.model.set_images_in_stack(uuid, images)

    def add_180_deg_to_sample(self, stack_name: str, _180_deg_file: str):
        return self.model.add_180_deg_to_stack(stack_name, _180_deg_file)

    def create_stack_name(self, filename: str):
        return self.model.create_name(os.path.basename(filename))

    def add_projection_angles_to_sample(self, stack_name: str, proj_angles: ProjectionAngles):
        self.model.add_projection_angles_to_sample(stack_name, proj_angles)

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

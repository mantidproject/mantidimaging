import os
import traceback
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING, Union
from uuid import UUID

from PyQt5.QtWidgets import QDockWidget

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.stack_visualiser.presenter import SVNotification
from .model import MainWindowModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView


class Notification(Enum):
    LOAD = 1
    SAVE = 2


class MainWindowPresenter(BasePresenter):
    LOAD_ERROR_STRING = "Failed to load stack. Error: {}"
    SAVE_ERROR_STRING = "Failed to save stack. Error: {}"

    view: 'MainWindowView'

    def __init__(self, view):
        super(MainWindowPresenter, self).__init__(view)
        self.model = MainWindowModel()

    def notify(self, signal):
        try:
            if signal == Notification.LOAD:
                self.load_stack()
            elif signal == Notification.SAVE:
                self.save()

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def remove_stack(self, uuid: UUID):
        self.model.do_remove_stack(uuid)
        self.view.active_stacks_changed.emit()

    def rename_stack_by_name(self, old_name: str, new_name: str):
        dock = self.model.get_stack_by_name(old_name)
        if dock:
            dock.setWindowTitle(new_name)
            self.view.active_stacks_changed.emit()

    def load_stack(self, **kwargs):
        if kwargs:
            raise NotImplementedError("Converting from kwargs to LoadParameters not implemented")
        par = self.view.load_dialogue.get_parameters()

        if par.sample.input_path == "":
            raise ValueError("No sample path provided")

        start_async_task_view(self.view, self.model.do_load_stack, self._on_stack_load_done, {'parameters': par})

    def _on_stack_load_done(self, task):
        log = getLogger(__name__)

        if task.was_successful():
            title = task.kwargs['parameters'].name
            self.create_new_stack(task.result, title)
            task.result = None
        else:
            self._handle_task_error(self.LOAD_ERROR_STRING, log, task)

    def _handle_task_error(self, base_message: str, log, task):
        # TODO add types
        msg = base_message.format(task.error)
        log.error(msg)
        self.show_error(msg, traceback.format_exc())

    def create_new_stack(self, container: Union[Images, Dataset], title: str):
        title = self.model.create_name(title)

        def add_stack(images: Images, title) -> QDockWidget:
            dock = self.view._create_stack_window(images, title=title)
            stack_visualiser = dock.widget()
            self.model.add_stack(stack_visualiser, dock)
            return dock

        sample = container if isinstance(container, Images) else container.sample
        sample_dock = add_stack(sample, title)

        if isinstance(container, Dataset):
            if container.flat and container.flat.filenames:
                flat_dock = add_stack(container.flat,
                                      title=f"{self.model.create_name(os.path.basename(container.flat.filenames[0]))}")
                self.view.tabifyDockWidget(sample_dock, flat_dock)

            if container.dark and container.dark.filenames:
                dark_dock = add_stack(container.dark,
                                      title=f"{self.model.create_name(os.path.basename(container.dark.filenames[0]))}")
                self.view.tabifyDockWidget(sample_dock, dark_dock)
            if container.sample.has_proj180deg() and container.sample.proj180deg.filenames:
                proj180_dock = add_stack(
                    container.sample.proj180deg,
                    title=f"{self.model.create_name(os.path.basename(container.sample.proj180deg.filenames[0]))}")
                self.view.tabifyDockWidget(sample_dock, proj180_dock)

        self.view.active_stacks_changed.emit()

    def save(self):
        kwargs = {
            'stack_uuid': self.view.save_dialogue.selected_stack,
            'output_dir': self.view.save_dialogue.save_path(),
            'name_prefix': self.view.save_dialogue.name_prefix(),
            'image_format': self.view.save_dialogue.image_format(),
            'overwrite': self.view.save_dialogue.overwrite()
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
        return self.model.stack_names

    def get_stack_visualiser(self, stack_uuid: UUID):
        return self.model.get_stack_visualiser(stack_uuid)

    def get_stack_history(self, stack_uuid: UUID):
        return self.model.get_stack_history(stack_uuid)

    @property
    def have_active_stacks(self):
        return self.model.have_active_stacks

    def update_stack_with_images(self, images):
        sv = self.model.get_stack_by_images(images)
        sv.presenter.notify(SVNotification.REFRESH_IMAGE)

from copy import deepcopy
from enum import Enum
from logging import getLogger
from typing import Any, Dict
from uuid import UUID

from mantidimaging.gui.dialogs.async_task import start_async_task_view
from mantidimaging.core.data import Images
from mantidimaging.gui.mvp_base import BasePresenter
from .model import MainWindowModel


class Notification(Enum):
    LOAD = 1
    SAVE = 2


class MainWindowPresenter(BasePresenter):
    LOAD_ERROR_STRING = "Failed to load stack. Error: {}"
    SAVE_ERROR_STRING = "Failed to save stack. Error: {}"

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
            self.show_error(e)
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
        kwargs = kwargs if kwargs else self.view.load_dialogue.get_kwargs()

        if 'sample_path' not in kwargs or not kwargs['sample_path']:
            raise ValueError("No sample path provided, cannot load anything")

        if 'staged_load' in kwargs and kwargs['staged_load']:
            self.execute_staged_load(kwargs)
        else:
            start_async_task_view(self.view, self.model.do_load_stack, self._on_stack_load_done, kwargs)

    def execute_staged_load(self, kwargs: Dict[str, Any]) -> None:
        """
        Starts a task to load a preview of the stack and another to load the stack with the original step size.

        :param kwargs: the parameters to use for loading
        """
        # Set the 'preview' to load 1/10 of the images
        preview_kwargs = deepcopy(kwargs)
        indices = kwargs['indices']
        preview_kwargs['indices'] = indices.start, indices.end, (indices.end - indices.start) // 10

        if 'custom_name' not in preview_kwargs or not preview_kwargs['custom_name']:
            preview_kwargs['custom_name'] = preview_kwargs['selected_file'].split(".")[0] + "_preview"
        else:
            preview_kwargs['custom_name'] += "_preview"

        start_async_task_view(self.view, self.model.do_load_stack, self._on_stack_load_done, preview_kwargs)
        start_async_task_view(self.view, self.model.do_load_stack, self._on_stack_load_done, kwargs)

    def _on_stack_load_done(self, task):
        log = getLogger(__name__)

        if task.was_successful():
            custom_name = task.kwargs['custom_name']
            title = task.kwargs['selected_file'] if not custom_name else custom_name
            self.create_new_stack(task.result, title)
            del task.result
        else:
            self._handle_task_error(self.LOAD_ERROR_STRING, log, task)

    def _handle_task_error(self, base_message: str, log, task):
        # TODO add types
        msg = base_message.format(task.error)
        log.error(msg)
        self.show_error(msg)

    def create_new_stack(self, data: Images, title: str):
        title = self.model.create_name(title)
        dock_widget = self.view.create_stack_window(data, title=title)
        stack_visualiser = dock_widget.widget()
        self.model.add_stack(stack_visualiser, dock_widget)
        self.view.active_stacks_changed.emit()

    def save(self):
        kwargs = {
            'stack_uuid': self.view.save_dialogue.selected_stack,
            'output_dir': self.view.save_dialogue.save_path(),
            'name_prefix': self.view.save_dialogue.name_prefix(),
            'image_format': self.view.save_dialogue.image_format(),
            'overwrite': self.view.save_dialogue.overwrite(),
            'swap_axes': self.view.save_dialogue.swap_axes()
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

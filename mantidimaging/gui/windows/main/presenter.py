from enum import Enum
from logging import getLogger
from uuid import UUID

from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.dialogs.async_task import AsyncTaskDialogView
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

    def remove_stack(self, uuid):
        self.model.do_remove_stack(uuid)
        self.view.active_stacks_changed.emit()

    def load_stack(self, kwargs=None):
        log = getLogger(__name__)

        if not kwargs:
            kwargs = {'selected_file': self.view.load_dialogue.sample_file(),
                      'sample_path': self.view.load_dialogue.sample_path_directory(),
                      'flat_path': self.view.load_dialogue.flat_path_directory(),
                      'dark_path': self.view.load_dialogue.dark_path_directory(),
                      'image_format': self.view.load_dialogue.image_format,
                      'parallel_load': self.view.load_dialogue.parallel_load(),
                      'indices': self.view.load_dialogue.indices(),
                      'custom_name': self.view.load_dialogue.window_title()}

        if not kwargs['sample_path']:
            log.debug("No sample path provided, cannot load anything")
            return

        self.start_async_task(kwargs, self.model.do_load_stack, self._on_stack_load_done)

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

    def create_new_stack(self, data, title):
        title = self.model.create_name(title)
        dock_widget = self.view.create_stack_window(data, title=title)
        stack_visualiser = dock_widget.widget()
        self.model.add_stack(stack_visualiser, dock_widget)
        self.view.active_stacks_changed.emit()

    def save(self, indices=None):
        kwargs = {'stack_uuid': self.view.save_dialogue.selected_stack,
                  'output_dir': self.view.save_dialogue.save_path(),
                  'name_prefix': self.view.save_dialogue.name_prefix(),
                  'image_format': self.view.save_dialogue.image_format(),
                  'overwrite': self.view.save_dialogue.overwrite(), 'swap_axes': self.view.save_dialogue.swap_axes(),
                  'indices': indices}

        self.start_async_task(kwargs, self.model.do_saving, self._on_save_done)

    def start_async_task(self, kwargs, task, on_complete):
        atd = AsyncTaskDialogView(self.view, auto_close=True)
        kwargs['progress'] = Progress()
        kwargs['progress'].add_progress_handler(atd.presenter)
        atd.presenter.set_task(task)
        atd.presenter.set_on_complete(on_complete)
        atd.presenter.set_parameters(**kwargs)
        atd.presenter.do_start_processing()

    def _on_save_done(self, task):
        log = getLogger(__name__)

        if not task.was_successful():
            self._handle_task_error(self.SAVE_ERROR_STRING, log, task)

    def stack_list(self):
        return self.model.stack_list()

    def stack_uuids(self):
        return self.model.stack_uuids()

    def stack_names(self):
        return self.model.stack_names()

    def get_stack_visualiser(self, stack_uuid: UUID):
        return self.model.get_stack_visualiser(stack_uuid)

    @property
    def have_active_stacks(self):
        return self.model.have_active_stacks

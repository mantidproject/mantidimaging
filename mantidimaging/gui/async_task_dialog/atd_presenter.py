from __future__ import absolute_import, division, print_function

from enum import Enum

from .atd_model import AsyncTaskDialogModel


class Notification(Enum):
    START = 1


class AsyncTaskDialogPresenter(object):
    def __init__(self, view):
        self.view = view
        self.model = AsyncTaskDialogModel()
        self.model.task_done.connect(self.view.handle_completion)

    def notify(self, signal):
        try:
            if signal == Notification.START:
                self.do_start_processing()
        except Exception as e:
            self.show_error(e)
            raise  # re-raise for full stack trace

    def set_task(self, f):
        self.model.task.task_function = f

    def set_parameters(self, *args, **kwargs):
        self.model.task.args = args
        self.model.task.kwargs = kwargs

    def set_on_complete(self, f):
        self.model.on_complete_function = f

    def do_start_processing(self):
        """
        Starts async task execution and shows GUI.
        """
        self.model.do_execute_async()
        self.view.show()

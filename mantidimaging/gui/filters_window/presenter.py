from __future__ import absolute_import, division, print_function

from enum import Enum

from .model import FiltersWindowModel


class Notification(Enum):
    UPDATE_STACK_LIST = 1


class FiltersWindowPresenter(object):
    def __init__(self, view, main_window):
        super(FiltersWindowPresenter, self).__init__()

        self.view = view
        self.model = FiltersWindowModel()

        self.main_window = main_window

        # Refresh the stack list in the algorithm dialog whenever the active
        # stacks change
        self.main_window.active_stacks_changed.connect(self.update_stack_list)

    def notify(self, signal):
        try:
            if signal == Notification.UPDATE_STACK_LIST:
                self.update_stack_list()

        except Exception as e:
            self.show_error(e)
            raise  # re-raise for full stack trace

    def show_error(self, error):
        self.view.show_error_dialog(error)

    def update_stack_list(self):
        # Clear the previous entries from the drop down menu
        self.view.stackSelector.clear()

        # Get all the new stacks
        stack_list = self.main_window.stack_list()
        if stack_list:
            self.stack_uuids, user_friendly_names = zip(*stack_list)
            self.view.stackSelector.addItems(user_friendly_names)

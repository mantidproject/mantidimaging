from __future__ import absolute_import, division, print_function

from enum import Enum
from logging import getLogger

from .model import FiltersWindowModel


class Notification(Enum):
    UPDATE_STACK_LIST = 1
    REGISTER_ACTIVE_FILTER = 2
    APPLY_FILTER = 3


class FiltersWindowPresenter(object):
    def __init__(self, view, main_window):
        super(FiltersWindowPresenter, self).__init__()

        self.view = view
        self.model = FiltersWindowModel(main_window)

        self.main_window = main_window

        # Refresh the stack list in the algorithm dialog whenever the active
        # stacks change
        self.main_window.active_stacks_changed.connect(
                lambda: self.notify(Notification.UPDATE_STACK_LIST))

    def notify(self, signal):
        try:
            if signal == Notification.UPDATE_STACK_LIST:
                self.do_update_stack_list()
            elif signal == Notification.REGISTER_ACTIVE_FILTER:
                self.do_register_active_filter()
            elif signal == Notification.APPLY_FILTER:
                self.do_apply_filter()

        except Exception as e:
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    def show_error(self, error):
        self.view.show_error_dialog(error)

    def do_update_stack_list(self):
        """
        Refreshes the stack list and UUID cache.

        Must be called at least once before the UI is shown.
        """
        # Clear the previous entries from the drop down menu
        self.view.stackSelector.clear()

        # Get all the new stacks
        stack_list = self.main_window.stack_list()
        if stack_list:
            self.model.stack_uuids, user_friendly_names = zip(*stack_list)
            self.view.stackSelector.addItems(user_friendly_names)

    def do_register_active_filter(self):
        filter_idx = self.view.filterSelector.currentIndex()

        # Get registration function for new filter
        register_func = \
            self.model.filter_registration_func(filter_idx)

        # Register new filter (adding it's property widgets to the properties
        # layout)
        self.model.setup_filter(
                register_func(self.view.filterPropertiesLayout))

    def do_apply_filter(self):
        self.model.stack_idx = self.view.stackSelector.currentIndex()
        self.model.do_apply_filter()

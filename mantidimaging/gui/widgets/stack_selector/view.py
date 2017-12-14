from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from .presenter import (
        StackSelectorWidgetPresenter, Notification)


class StackSelectorWidgetView(Qt.QComboBox):

    stacks_updated = Qt.pyqtSignal()

    stack_selected_int = Qt.pyqtSignal(int)
    stack_selected_uuid = Qt.pyqtSignal('PyQt_PyObject')

    def __init__(self, parent):
        super(StackSelectorWidgetView, self).__init__(parent)

        self.presenter = StackSelectorWidgetPresenter(self)

        self.currentIndexChanged[int].connect(self.presenter.handle_selection)

    def subscribe_to_main_window(self, main_window):
        self.main_window = main_window

        # Initial population of stack list
        self.presenter.notify(Notification.RELOAD_STACKS)

        # Connect signal for auto update on stack change
        self.main_window.active_stacks_changed.connect(
                lambda: self.presenter.notify(Notification.RELOAD_STACKS))

from typing import TYPE_CHECKING

from PyQt5 import Qt

from .presenter import (StackSelectorWidgetPresenter, Notification)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView


class StackSelectorWidgetView(Qt.QComboBox):
    stacks_updated = Qt.pyqtSignal()

    stack_selected_int = Qt.pyqtSignal(int)
    stack_selected_uuid = Qt.pyqtSignal('PyQt_PyObject')

    main_window: 'MainWindowView'

    def __init__(self, parent):
        super(StackSelectorWidgetView, self).__init__(parent)

        self.presenter = StackSelectorWidgetPresenter(self)

        self.currentIndexChanged[int].connect(self.presenter.handle_selection)

    def subscribe_to_main_window(self, main_window: 'MainWindowView'):
        self.main_window = main_window

        # Initial population of stack list
        self.presenter.notify(Notification.RELOAD_STACKS)

        # Connect signal for auto update on stack change
        self.main_window.active_stacks_changed.connect(self._handle_loaded_stacks_changed)

    def unsubscribe_from_main_window(self):
        """
        Removes connections to main window.

        Must be called before the widget is destroyed.
        """
        if self.main_window:
            # Disconnect signal
            self.main_window.active_stacks_changed.disconnect(self._handle_loaded_stacks_changed)

    def _handle_loaded_stacks_changed(self):
        """
        Handle a change in loaded stacks.
        """
        self.presenter.notify(Notification.RELOAD_STACKS)

    def current(self):
        return self.presenter.current_stack

    def select_eligible_stack(self):
        self.presenter.notify(Notification.SELECT_ELIGIBLE_STACK)
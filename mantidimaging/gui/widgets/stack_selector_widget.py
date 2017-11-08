from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from mantidimaging.gui.utility import BlockQtSignals


class StackSelectorWidget(Qt.QComboBox):

    stacks_updated = Qt.pyqtSignal()

    stack_selected_int = Qt.pyqtSignal(int)
    stack_selected_uuid = Qt.pyqtSignal('PyQt_PyObject')

    def __init__(self, parent):
        super(StackSelectorWidget, self).__init__(parent)

        self.stack_uuids = []

        self.currentIndexChanged[int].connect(self.handle_selection)

    def subscribe_to_main_window(self, main_window):
        self.main_window = main_window

        self.main_window.active_stacks_changed.connect(
                self.reload_stacks)

    def reload_stacks(self):
        # Don't want signals emitted when changing the list of stacks
        with BlockQtSignals([self]):
            # Clear the previous entries from the drop down menu
            self.clear()

            # Get all the new stacks
            stack_list = self.main_window.stack_list()
            self.stack_uuids, user_friendly_names = \
                zip(*stack_list) if stack_list else (None, [])
            self.addItems(user_friendly_names)

            # Default to the first item
            self.setCurrentIndex(0)

        self.stacks_updated.emit()
        self.handle_selection(0)

    def handle_selection(self, index):
        self.stack_selected_int.emit(index)

        uuid = self.stack_uuids[index] if self.stack_uuids else None
        self.stack_selected_uuid.emit(uuid)

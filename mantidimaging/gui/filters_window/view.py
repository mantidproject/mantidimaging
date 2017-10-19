from __future__ import absolute_import, division, print_function

from PyQt5 import Qt, QtWidgets

from mantidimaging.gui.utility import compile_ui

from .presenter import FiltersWindowPresenter
from .presenter import Notification as PresNotification


def _delete_all_widgets_from_layout(lo):
    """
    Removes and deletes all child widgets form a layout.

    :param lo: Layout to clean
    """
    # For each item in the layout (removed as iterated)
    while(lo.count() > 0):
        item = lo.takeAt(0)

        # Recurse for child layouts
        if isinstance(item, Qt.QLayout):
            _delete_all_widgets_from_layout(item)

        # Orphan child widgets (seting a None parent removes them from the
        # layout and marks them for deletion)
        elif item.widget() is not None:
            item.widget().setParent(None)


class FiltersWindowView(Qt.QDialog):

    def __init__(self, main_window):
        super(FiltersWindowView, self).__init__()
        compile_ui('gui/ui/filters_window.ui', self)

        self.presenter = FiltersWindowPresenter(self, main_window)

        # Populate list of filters and handle filter selection
        self.filterSelector.addItems(self.presenter.model.filter_names)
        self.filterSelector.currentIndexChanged[int].connect(
                self.handle_filter_selection)
        self.handle_filter_selection(0)

        # Handle button clicks
        self.buttonBox.clicked.connect(self.handle_button)

        # Refresh the stack list in the algorithm dialog whenever the active
        # stacks change
        main_window.active_stacks_changed.connect(
                lambda: self.presenter.notify(
                    PresNotification.UPDATE_STACK_LIST))

    def show_error_dialog(self, msg=""):
        """
        Shows an error message.

        :param msg: Error message string
        """
        QtWidgets.QMessageBox.critical(self, "Error", str(msg))

    def show(self):
        self.presenter.notify(PresNotification.UPDATE_STACK_LIST)
        super(FiltersWindowView, self).show()

    def handle_button(self, button):
        """
        Handle button presses from the dialog button box.
        """
        role = self.buttonBox.buttonRole(button)

        # If Apply was clicked
        if role == QtWidgets.QDialogButtonBox.ApplyRole:
            self.presenter.notify(PresNotification.APPLY_FILTER)

    def handle_filter_selection(self, filter_idx):
        """
        Handle selection of a filter from the drop down list.
        """
        # Remove all existing items from the properties layout
        _delete_all_widgets_from_layout(self.filterPropertiesLayout)

        # Do registration of new filter
        self.presenter.notify(PresNotification.REGISTER_ACTIVE_FILTER)

    @property
    def selected_stack_idx(self):
        """
        Gets the currently selected index on the stack selector.
        """
        return self.stackSelector.currentIndex()

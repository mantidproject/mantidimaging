from __future__ import absolute_import, division, print_function

from PyQt5 import Qt, QtWidgets

from mantidimaging.gui.utility import compile_ui

from .presenter import FiltersWindowPresenter
from .presenter import Notification as PresNotification


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
        # https://stackoverflow.com/a/13103617
        while(self.filterPropertiesLayout.count() > 0):
            self.filterPropertiesLayout.takeAt(0).widget().setParent(None)

        # Get registration function for new filter
        register_func = \
            self.presenter.model.filter_registration_func(filter_idx)

        # Register new filter (adding it's property widgets to the properties
        # layout)
        do_before, execute, do_after = \
            register_func(self.filterPropertiesLayout)

    @property
    def selected_stack_idx(self):
        """
        Gets the currently selected index on the stack selector.
        """
        return self.stackSelector.currentIndex()

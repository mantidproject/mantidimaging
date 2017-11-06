from __future__ import absolute_import, division, print_function

from PyQt5 import Qt, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from mantidimaging.gui.utility import (
        compile_ui, delete_all_widgets_from_layout)

from .navigation_toolbar import FiltersWindowNavigationToolbar
from .presenter import FiltersWindowPresenter
from .presenter import Notification as PresNotification


class FiltersWindowView(Qt.QDialog):

    auto_update_triggered = Qt.pyqtSignal()

    def __init__(self, main_window, cmap='Greys_r'):
        super(FiltersWindowView, self).__init__()
        compile_ui('gui/ui/filters_window.ui', self)

        self.presenter = FiltersWindowPresenter(self, main_window)

        # Populate list of filters and handle filter selection
        self.filterSelector.addItems(self.presenter.model.filter_names)
        self.filterSelector.currentIndexChanged[int].connect(
                self.handle_filter_selection)
        self.handle_filter_selection(0)

        # Handle stack selection
        self.stackSelector.currentIndexChanged[int].connect(
                self.presenter.set_stack_index)
        self.stackSelector.currentIndexChanged[int].connect(
                self.auto_update_triggered.emit)

        # Handle button clicks
        self.buttonBox.clicked.connect(self.handle_button)

        # Refresh the stack list in the algorithm dialog whenever the active
        # stacks change
        main_window.active_stacks_changed.connect(
                lambda: self.presenter.notify(
                    PresNotification.UPDATE_STACK_LIST))

        # Preview area
        self.cmap = cmap

        self.figure = Figure(tight_layout=True)

        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setParent(self)

        self.toolbar = FiltersWindowNavigationToolbar(
                self.canvas, self)
        self.toolbar.filter_window = self

        self.mplLayout.addWidget(self.toolbar)
        self.mplLayout.addWidget(self.canvas)

        def add_plot(num, title, **kwargs):
            plt = self.figure.add_subplot(num, title=title, **kwargs)
            return plt

        self.preview_image_before = add_plot(
                221, 'Image Before')

        self.preview_image_after = add_plot(
                223, 'Image After',
                sharex=self.preview_image_before,
                sharey=self.preview_image_before)

        self.preview_histogram_before = add_plot(
                222, 'Histogram Before')
        self.preview_histogram_before.plot([], [])

        self.preview_histogram_after = add_plot(
                224, 'Histogram After',
                sharex=self.preview_histogram_before,
                sharey=self.preview_histogram_before)
        self.preview_histogram_after.plot([], [])

        # Handle preview index selection
        self.previewImageIndex.valueChanged[int].connect(
                self.presenter.set_preview_image_index)

        # Preview update triggers
        self.auto_update_triggered.connect(self.on_auto_update_triggered)
        self.updatePreviewButton.clicked.connect(
            lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))

    def show_error_dialog(self, msg=""):
        """
        Shows an error message.

        :param msg: Error message string
        """
        QtWidgets.QMessageBox.critical(self, "Error", str(msg))

    def show(self):
        self.presenter.notify(PresNotification.UPDATE_STACK_LIST)
        super(FiltersWindowView, self).show()
        self.auto_update_triggered.emit()

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
        delete_all_widgets_from_layout(self.filterPropertiesLayout)

        # Do registration of new filter
        self.presenter.notify(PresNotification.REGISTER_ACTIVE_FILTER)

        # Update preview on filter selection (on the off chance the default
        # options are valid)
        self.auto_update_triggered.emit()

    def on_auto_update_triggered(self):
        """
        Called when the signal indicating the filter, filter properties or data
        has changed such that the previews are now out of date.
        """
        if self.previewAutoUpdate.isChecked() and self.isVisible():
            self.presenter.notify(PresNotification.UPDATE_PREVIEWS)

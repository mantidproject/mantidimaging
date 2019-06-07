from PyQt5 import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility import (
    delete_all_widgets_from_layout)

from mantidimaging.gui.windows.filters.navigation_toolbar import FiltersWindowNavigationToolbar
from mantidimaging.gui.windows.savu_filters.presenter import SavuFiltersWindowPresenter
from mantidimaging.gui.windows.savu_filters.presenter import Notification as PresNotification


class SavuFiltersWindowView(BaseMainWindowView):
    auto_update_triggered = Qt.pyqtSignal()

    def __init__(self, main_window, cmap='Greys_r'):
        super(SavuFiltersWindowView, self).__init__(
            main_window, 'gui/ui/filters_window.ui')

        self.presenter = SavuFiltersWindowPresenter(self, main_window)

        # Populate list of filters and handle filter selection
        self.filterSelector.addItems(self.presenter.model.filter_names)
        self.filterSelector.currentIndexChanged[int].connect(
            self.handle_filter_selection)
        self.handle_filter_selection(0)

        # Handle stack selection
        self.stackSelector.stack_selected_uuid.connect(
            self.presenter.set_stack_uuid)
        self.stackSelector.stack_selected_uuid.connect(
            self.auto_update_triggered.emit)

        # Handle apply filter
        self.applyButton.clicked.connect(
            lambda: self.presenter.notify(PresNotification.APPLY_FILTER))

        # Preview area
        self.cmap = cmap

        self.figure = Figure(tight_layout=True)

        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setParent(self)

        self.toolbar = FiltersWindowNavigationToolbar(self.canvas, self)
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

        self.clear_preview_plots()

        # Handle preview index selection
        self.previewImageIndex.valueChanged[int].connect(
            self.presenter.set_preview_image_index)

        # Preview update triggers
        self.auto_update_triggered.connect(self.on_auto_update_triggered)
        self.updatePreviewButton.clicked.connect(
            lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))

        self.stackSelector.subscribe_to_main_window(main_window)

    def cleanup(self):
        self.stackSelector.unsubscribe_from_main_window()

    def show(self):
        super(SavuFiltersWindowView, self).show()
        self.auto_update_triggered.emit()

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

    def clear_preview_plots(self):
        """
        Clears the plotted data from the preview images and plots.
        """
        self.preview_image_before.cla()
        self.preview_image_after.cla()

        self.preview_histogram_before.lines[0].set_data([], [])
        self.preview_histogram_after.lines[0].set_data([], [])

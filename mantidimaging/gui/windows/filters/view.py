from typing import TYPE_CHECKING

from PyQt5 import Qt
from PyQt5.QtWidgets import QVBoxLayout
from pyqtgraph import GraphicsLayoutWidget, ImageItem, PlotItem, ViewBox

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility import (
    delete_all_widgets_from_layout)
from .presenter import FiltersWindowPresenter
from .presenter import Notification as PresNotification

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401


class FiltersWindowView(BaseMainWindowView):
    auto_update_triggered = Qt.pyqtSignal()

    previewsLayout: QVBoxLayout

    def __init__(self, main_window: 'MainWindowView'):
        super(FiltersWindowView, self).__init__(main_window, 'gui/ui/filters_window.ui')

        self.main_window = main_window
        self.presenter = FiltersWindowPresenter(self, main_window)

        # Populate list of filters and handle filter selection
        self.filterSelector.addItems(self.presenter.model.filter_names)
        self.filterSelector.currentIndexChanged[int].connect(
            self.handle_filter_selection)
        self.handle_filter_selection(0)

        # Handle stack selection
        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)
        self.stackSelector.stack_selected_uuid.connect(self.auto_update_triggered.emit)

        # Handle apply filter
        self.applyButton.clicked.connect(lambda: self.presenter.notify(PresNotification.APPLY_FILTER))

        histogram_axes_labels = {'left': 'Frequency', 'bottom': 'Value'}
        self.previews: GraphicsLayoutWidget = GraphicsLayoutWidget()
        self.previewsLayout.addWidget(self.previews)

        self.previews.addLabel("Image before:")
        self.previews.addLabel("Pixel values before:")
        self.previews.nextRow()

        self.preview_image_before: ImageItem = ImageItem()
        self.preview_image_before_vb: ViewBox = self.previews.addViewBox(invertY=True)
        self.preview_image_before_vb.addItem(self.preview_image_before)
        self.preview_histogram_before: PlotItem = self.previews.addPlot(labels=histogram_axes_labels)

        self.previews.nextRow()
        self.previews.addLabel("Image after:")
        self.previews.addLabel("Pixel values after:")
        self.previews.nextRow()

        self.preview_image_after: ImageItem = ImageItem()
        self.preview_image_after_vb = self.previews.addViewBox(invertY=True)
        self.preview_image_after_vb.addItem(self.preview_image_after)
        self.preview_histogram_after: PlotItem = self.previews.addPlot(labels=histogram_axes_labels)

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
        self.main_window.filters = None
        self.presenter = None

    def show(self):
        super(FiltersWindowView, self).show()
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
        self.preview_image_before.setImage()
        self.preview_image_after.setImage()
        self.preview_histogram_before.clear()
        self.preview_histogram_after.clear()

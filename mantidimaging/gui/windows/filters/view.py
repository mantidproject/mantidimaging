from typing import TYPE_CHECKING

from PyQt5 import Qt
from PyQt5.QtWidgets import QVBoxLayout
from pyqtgraph import ImageItem, PlotDataItem

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility import (
    delete_all_widgets_from_layout)
from .filter_previews import FilterPreviews
from .presenter import FiltersWindowPresenter
from .presenter import Notification as PresNotification

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401


class FiltersWindowView(BaseMainWindowView):
    auto_update_triggered = Qt.pyqtSignal()

    previewsLayout: QVBoxLayout
    previews: FilterPreviews

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

        self.previews = FilterPreviews()
        self.previewsLayout.addWidget(self.previews)
        self.clear_previews()

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

    def clear_previews(self):
        self.previews.clear_items()

    @property
    def preview_image_before(self) -> ImageItem:
        return self.previews.image_before

    @property
    def preview_image_after(self) -> ImageItem:
        return self.previews.image_after

    @property
    def preview_histogram_before(self) -> PlotDataItem:
        return self.previews.histogram_plot_before

    @property
    def preview_histogram_after(self) -> PlotDataItem:
        return self.previews.histogram_plot_after

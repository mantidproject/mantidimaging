from typing import TYPE_CHECKING

from PyQt5 import Qt
from PyQt5.QtWidgets import QVBoxLayout, QCheckBox, QLabel, QApplication, QSplitter, QPushButton
from pyqtgraph import ImageItem

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility import (delete_all_widgets_from_layout)
from mantidimaging.gui.widgets.stack_selector import StackSelectorWidgetView
from .filter_previews import FilterPreviews
from .presenter import FiltersWindowPresenter
from .presenter import Notification as PresNotification

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401


class FiltersWindowView(BaseMainWindowView):
    auto_update_triggered = Qt.pyqtSignal()

    splitter: QSplitter

    linkImages: QCheckBox
    invertDifference: QCheckBox
    showHistogramLegend: QCheckBox
    combinedHistograms: QCheckBox

    previewsLayout: QVBoxLayout
    previews: FilterPreviews
    stackSelector: StackSelectorWidgetView

    error_icon: QLabel
    error_text: QLabel

    presenter: FiltersWindowPresenter

    applyButton: QPushButton

    def __init__(self, main_window: 'MainWindowView'):
        super(FiltersWindowView, self).__init__(main_window, 'gui/ui/filters_window.ui')

        self.main_window = main_window
        self.presenter = FiltersWindowPresenter(self, main_window)
        self.splitter.setStretchFactor(0, 0)

        # Populate list of filters and handle filter selection
        self.filterSelector.addItems(self.presenter.model.filter_names)
        self.filterSelector.currentIndexChanged[int].connect(self.handle_filter_selection)
        self.handle_filter_selection(0)

        # Handle stack selection
        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)
        self.stackSelector.stack_selected_uuid.connect(self.auto_update_triggered.emit)

        # Handle apply filter
        self.applyButton.clicked.connect(lambda: self.presenter.notify(PresNotification.APPLY_FILTER))

        self.previews = FilterPreviews(self)
        self.previewsLayout.addWidget(self.previews)
        self.clear_previews()

        self.combinedHistograms.stateChanged.connect(self.histogram_mode_changed)
        self.showHistogramLegend.stateChanged.connect(self.histogram_legend_is_changed)
        # set here to trigger the changed event
        self.showHistogramLegend.setChecked(True)

        self.linkImages.stateChanged.connect(self.link_images_changed)
        # set here to trigger the changed event
        self.linkImages.setChecked(True)
        self.invertDifference.stateChanged.connect(lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))

        # Handle preview index selection
        self.previewImageIndex.valueChanged[int].connect(self.presenter.set_preview_image_index)

        # Preview update triggers
        self.auto_update_triggered.connect(self.on_auto_update_triggered)
        self.updatePreviewButton.clicked.connect(lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))

        self.stackSelector.subscribe_to_main_window(main_window)

    def cleanup(self):
        self.stackSelector.unsubscribe_from_main_window()
        self.presenter.disconnect_current_stack_roi()
        self.auto_update_triggered.disconnect()
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

    def histogram_mode_changed(self):
        self.previews.combined_histograms = self.combinedHistograms.isChecked()
        self.previews.redraw_histograms()

    def histogram_legend_is_changed(self):
        self.previews.histogram_legend_visible = self.showHistogramLegend.isChecked()
        legend = self.previews.histogram_legend
        if legend:
            if self.showHistogramLegend.isChecked():
                legend.show()
            else:
                legend.hide()

    def link_images_changed(self):
        if self.linkImages.isChecked():
            self.previews.link_all_views()
        else:
            self.previews.unlink_all_views()

    @property
    def preview_image_before(self) -> ImageItem:
        return self.previews.image_before

    @property
    def preview_image_after(self) -> ImageItem:
        return self.previews.image_after

    @property
    def preview_image_difference(self) -> ImageItem:
        return self.previews.image_difference

    def show_error_dialog(self, msg=""):
        self.error_text.show()
        self.error_icon.setPixmap(QApplication.style().standardPixmap(QApplication.style().SP_MessageBoxCritical))
        self.error_text.setText(str(msg))

    def clear_error_dialog(self):
        self.error_icon.clear()
        self.error_text.clear()
        self.error_text.hide()

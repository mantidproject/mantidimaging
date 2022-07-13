# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import TYPE_CHECKING

import numpy as np
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox, QLabel, QMainWindow, QMenu, QMessageBox,
                             QPushButton, QSizePolicy, QSplitter, QStyle, QVBoxLayout)
from pyqtgraph import ImageItem

from mantidimaging.core.net.help_pages import open_user_operation_docs
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility import delete_all_widgets_from_layout
from mantidimaging.gui.widgets.mi_image_view.view import MIImageView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

from .filter_previews import FilterPreviews
from .presenter import FiltersWindowPresenter
from .presenter import Notification as PresNotification

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover


def _strip_filter_name(filter_name: str):
    """
    Removes hyphens and spaces from a filter name and makes it all lower case.
    :param filter_name: The human-readable filter name.
    :return: The stripped filter name.
    """
    return filter_name.lower().replace("-", "").replace(" ", "")


class FiltersWindowView(BaseMainWindowView):
    auto_update_triggered = pyqtSignal()
    filter_applied = pyqtSignal()

    splitter: QSplitter
    collapseToggleButton: QPushButton

    linkImages: QCheckBox
    invertDifference: QCheckBox
    overlayDifference: QCheckBox
    lockScaleCheckBox: QCheckBox
    lockZoomCheckBox: QCheckBox

    previewsLayout: QVBoxLayout
    previews: FilterPreviews
    stackSelector: DatasetSelectorWidgetView

    notification_icon: QLabel
    notification_text: QLabel

    presenter: FiltersWindowPresenter

    applyButton: QPushButton
    applyToAllButton: QPushButton
    filterSelector: QComboBox

    def __init__(self, main_window: 'MainWindowView'):
        super().__init__(main_window, 'gui/ui/filters_window.ui')

        self.main_window = main_window
        self.presenter = FiltersWindowPresenter(self, main_window)
        self.roi_view = None
        self.roi_view_averaged = False
        self.splitter.setSizes([200, 9999])
        self.splitter.setStretchFactor(0, 1)

        # Populate list of operations and handle filter selection
        self.filterSelector.addItems(self.presenter.model.filter_names)
        self.filterSelector.currentTextChanged.connect(self.handle_filter_selection)
        self.filterSelector.currentTextChanged.connect(self._update_apply_all_button)

        # Handle stack selection
        self.stackSelector.presenter.show_stacks = True
        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)
        self.stackSelector.stack_selected_uuid.connect(self.auto_update_triggered.emit)

        # Handle apply filter
        self.applyButton.clicked.connect(lambda: self.presenter.notify(PresNotification.APPLY_FILTER))
        self.applyToAllButton.clicked.connect(lambda: self.presenter.notify(PresNotification.APPLY_FILTER_TO_ALL))

        self.previews = FilterPreviews(self)
        self.previews.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.previewsLayout.addWidget(self.previews)
        self.clear_previews()

        self.linkImages.stateChanged.connect(self.link_images_changed)
        # set here to trigger the changed event
        self.linkImages.setChecked(True)
        self.invertDifference.stateChanged.connect(lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))
        self.overlayDifference.stateChanged.connect(lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))
        self.lockZoomCheckBox.stateChanged.connect(self.lock_zoom_changed)
        self.lockScaleCheckBox.stateChanged.connect(self.lock_scale_changed)

        # Handle preview index selection
        self.previewImageIndex.valueChanged[int].connect(self.presenter.set_preview_image_index)
        self.previews.z_slider.valueChanged.connect(self.presenter.set_preview_image_index)

        # Preview update triggers
        self.auto_update_triggered.connect(self.on_auto_update_triggered)
        self.previewAutoUpdate.stateChanged.connect(self.handle_auto_update_preview_selection)
        self.updatePreviewButton.clicked.connect(lambda: self.presenter.notify(PresNotification.UPDATE_PREVIEWS))

        self.stackSelector.subscribe_to_main_window(main_window)
        self.stackSelector.select_eligible_stack()

        # Handle help button pressed
        self.filterHelpButton.pressed.connect(self.open_help_webpage)
        self.collapseToggleButton.pressed.connect(self.toggle_filters_section)

        self.handle_filter_selection("")

    def closeEvent(self, e):
        if self.presenter.filter_is_running:
            e.ignore()
        else:
            super().closeEvent(e)

    def cleanup(self):
        self.stackSelector.unsubscribe_from_main_window()
        if self.roi_view is not None:
            self.roi_view.close()
            self.roi_view = None
        self.presenter.set_stack(None)
        self.auto_update_triggered.disconnect()
        self.main_window.filters = None
        self.presenter.view = None
        self.presenter = None

    def show(self):
        super().show()
        self.auto_update_triggered.emit()

    def handle_filter_selection(self, filter_name: str):
        """
        Handle selection of a filter from the drop down list.
        """
        # If a divider select the one below the divider.
        if filter_name == self.presenter.divider:
            self.filterSelector.setCurrentIndex(self.filterSelector.currentIndex() + 1)
            # Changing the selection triggers a second run through of this method that results in unwanted popups
            # Terminating the original call here ensures that the presenter is only notified once
            return

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
        # Disable the preview image box widget as it can misbehave if making a preview takes too long
        self.previewImageIndex.setEnabled(False)

        self.clear_notification_dialog()
        if self.previewAutoUpdate.isChecked() and self.isVisible():
            self.presenter.notify(PresNotification.UPDATE_PREVIEWS)

        # Enable the spinbox widget once the preview has been created
        self.previewImageIndex.setEnabled(True)

    def handle_auto_update_preview_selection(self):
        if self.previewAutoUpdate.isChecked():
            self.presenter.notify(PresNotification.UPDATE_PREVIEWS)

    def clear_previews(self, clear_before: bool = True):
        self.previews.clear_items(clear_before=clear_before)

    def link_images_changed(self):
        if self.linkImages.isChecked():
            self.previews.link_all_views()
        else:
            self.previews.unlink_all_views()

    @property
    def preview_image_before(self) -> ImageItem:
        return self.previews.imageview_before

    @property
    def preview_image_after(self) -> ImageItem:
        return self.previews.imageview_after

    @property
    def preview_image_difference(self) -> ImageItem:
        return self.previews.imageview_difference

    def show_error_dialog(self, msg=""):
        self.notification_text.show()
        self.notification_icon.setPixmap(QApplication.style().standardPixmap(QStyle.SP_MessageBoxCritical))
        self.notification_text.setText(str(msg))

    def clear_notification_dialog(self):
        self.notification_icon.clear()
        self.notification_text.clear()
        self.notification_text.hide()

    def show_operation_completed(self, operation_name):
        self.notification_text.show()
        self.notification_icon.setPixmap(QApplication.style().standardPixmap(QStyle.SP_DialogYesButton))
        self.notification_text.setText(f"{operation_name} completed successfully!")

    def show_operation_cancelled(self, operation_name):
        self.notification_text.show()
        self.notification_icon.setPixmap(QApplication.style().standardPixmap(QStyle.SP_DialogYesButton))
        self.notification_text.setText(f"{operation_name} cancelled, original data restored")

    def open_help_webpage(self):
        filter_name = self.filterSelector.currentText()

        try:
            open_user_operation_docs(filter_name)
        except RuntimeError as err:
            self.show_error_dialog(str(err))

    def ask_confirmation(self, msg: str):
        response = QMessageBox.question(self, "Confirm action", msg, QMessageBox.Ok | QMessageBox.Cancel)  # type:ignore
        return response == QMessageBox.Ok

    def _update_apply_all_button(self, filter_name):
        list_of_apply_single_stack = ["ROI Normalisation", "Flat-fielding"]
        if filter_name in list_of_apply_single_stack:
            self.applyToAllButton.setEnabled(False)
        else:
            self.applyToAllButton.setEnabled(True)

    def roi_visualiser(self, roi_field):
        # Start the stack visualiser and ensure that it uses the ROI from here in the rest of this
        try:
            images = self.presenter.stack.slice_as_image_stack(self.presenter.model.preview_image_idx)
        except IndexError:
            # Happens if nothing has been loaded, so do nothing as nothing can't be visualised
            return

        window = QMainWindow(self)
        window.setWindowTitle("Select ROI")
        window.setMinimumHeight(600)
        window.setMinimumWidth(600)
        self.roi_view = MIImageView(window)
        window.setCentralWidget(self.roi_view)
        self.roi_view.setWindowTitle("Select ROI for operation")

        def set_averaged_image():
            averaged_images = np.sum(self.presenter.stack.data, axis=0)
            self.roi_view.setImage(averaged_images.reshape((1, averaged_images.shape[0], averaged_images.shape[1])))
            self.roi_view_averaged = True

        def toggle_average_images(images_):
            if self.roi_view_averaged:
                self.roi_view.setImage(images_.data)
                self.roi_view_averaged = False
            else:
                set_averaged_image()
            self.roi_view.roi.show()
            self.roi_view.ui.roiPlot.hide()

        # Add context menu bits:
        menu = QMenu(self.roi_view)
        toggle_show_averaged_image = QAction("Toggle show averaged image", menu)
        toggle_show_averaged_image.triggered.connect(lambda: toggle_average_images(images))
        menu.addAction(toggle_show_averaged_image)
        menu.addSeparator()
        self.roi_view.imageItem.menu = menu

        set_averaged_image()

        def roi_changed_callback(callback):
            roi_field.setText(callback.to_list_string())
            roi_field.editingFinished.emit()

        self.roi_view.roi_changed_callback = lambda callback: roi_changed_callback(callback)

        # prep the MIImageView to display in this context
        self.roi_view.ui.roiBtn.hide()
        self.roi_view.ui.histogram.hide()
        self.roi_view.ui.menuBtn.hide()
        self.roi_view.ui.roiPlot.hide()
        self.roi_view.roi.show()
        self.roi_view.ui.gridLayout.setRowStretch(1, 5)
        self.roi_view.ui.gridLayout.setRowStretch(0, 95)
        self.roi_view.button_stack_right.hide()
        self.roi_view.button_stack_left.hide()
        button = QPushButton("OK", window)
        button.clicked.connect(lambda: window.close())
        self.roi_view.ui.gridLayout.addWidget(button)

        window.show()

    def toggle_filters_section(self):
        if self.collapseToggleButton.text() == "<<":
            self.splitter.setSizes([0, 9999])
            self.collapseToggleButton.setText(">>")
        else:
            self.splitter.setSizes([200, 9999])
            self.collapseToggleButton.setText("<<")

    def lock_zoom_changed(self):
        if not self.lockZoomCheckBox.isChecked():
            self.previews.auto_range()

    def lock_scale_changed(self):
        if not self.lockScaleCheckBox.isChecked():
            self.presenter.notify(PresNotification.UPDATE_PREVIEWS)

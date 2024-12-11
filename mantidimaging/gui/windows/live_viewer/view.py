# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtCore import QSignalBlocker, Qt
from PyQt5.QtWidgets import QVBoxLayout, QSplitter
from PyQt5.Qt import QAction, QActionGroup

from mantidimaging.gui.mvp_base import BaseMainWindowView
from .live_view_widget import LiveViewWidget
from .presenter import LiveViewerWindowPresenter

import numpy as np

from ..spectrum_viewer.spectrum_widget import SpectrumPlotWidget

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover


class LiveViewerWindowView(BaseMainWindowView):
    """
    Live Viewer window view class.
    This class is responsible for handling user interaction with the window.
    """

    imageLayout: QVBoxLayout

    def __init__(self, main_window: MainWindowView, live_dir_path: Path) -> None:
        super().__init__(None, 'gui/ui/live_viewer_window.ui')
        self.main_window = main_window
        self.path = live_dir_path
        self.setWindowTitle(f"Mantid Imaging - Live Viewer - {str(self.path)}")
        self.presenter = LiveViewerWindowPresenter(self, main_window)
        self.live_viewer = LiveViewWidget()
        self.splitter = QSplitter(Qt.Vertical)
        self.imageLayout.addWidget(self.splitter)
        self.live_viewer.z_slider.valueChanged.connect(self.presenter.select_image)

        self.spectrum_plot_widget = SpectrumPlotWidget()
        self.spectrum = self.spectrum_plot_widget.spectrum
        self.live_viewer.roi_changed.connect(self.presenter.handle_roi_moved)
        self.live_viewer.roi_changed_start.connect(self.presenter.handle_roi_moved_start)

        self.splitter.addWidget(self.live_viewer)
        self.splitter.addWidget(self.spectrum_plot_widget)
        widget_height = self.frameGeometry().height()
        self.splitter.setSizes([widget_height, 0])

        self.filter_params: dict[str, dict] = {}
        self.right_click_menu = self.live_viewer.image.vb.menu
        operations_menu = self.right_click_menu.addMenu("Operations")

        rotate_menu = operations_menu.addMenu("Rotate Image")
        self.rotate_angles_group = QActionGroup(self)
        allowed_angles = [0, 90, 180, 270]
        for angle in allowed_angles:
            action = QAction(str(angle) + "°", self.rotate_angles_group)
            action.setCheckable(True)
            rotate_menu.addAction(action)
            action.triggered.connect(self.set_image_rotation_angle)
            if angle == 0:
                action.setChecked(True)

        self.load_as_dataset_action = self.right_click_menu.addAction("Load as dataset")
        self.load_as_dataset_action.triggered.connect(self.presenter.load_as_dataset)

        self.spectrum_action = QAction("Calculate Spectrum", self)
        self.spectrum_action.setCheckable(True)
        operations_menu.addAction(self.spectrum_action)
        self.spectrum_action.triggered.connect(self.set_spectrum_visibility)
        self.live_viewer.set_roi_visibility_flags(False)

    def show(self) -> None:
        """Show the window"""
        super().show()
        self.activateWindow()
        self.watch_directory()

    def show_most_recent_image(self, image: np.ndarray) -> None:
        """
        Show the most recently modified image in the image view.
        @param image: The image to show
        """
        self.live_viewer.show_image(image)

    def watch_directory(self) -> None:
        """Show the most recent image arrived in the selected directory"""
        self.presenter.set_dataset_path(self.path)

    def remove_image(self) -> None:
        """Remove the image from the view."""
        self.live_viewer.handle_deleted()

    def set_image_range(self, index_range: tuple[int, int]) -> None:
        """Set the range on the z-slider, without triggering valueChanged signal"""
        with QSignalBlocker(self.live_viewer.z_slider):
            self.live_viewer.z_slider.set_range(*index_range)

    def set_image_index(self, index: int) -> None:
        """Set the position on the z-slider, triggering valueChanged signal once"""
        with QSignalBlocker(self.live_viewer.z_slider):
            self.live_viewer.z_slider.set_value(index)
        self.live_viewer.z_slider.valueChanged.emit(index)

    def closeEvent(self, e) -> None:
        """Close the window and remove it from the main window list"""
        self.main_window.live_viewer_list.remove(self)
        self.presenter.close()
        self.live_viewer.handle_deleted()
        super().closeEvent(e)
        self.presenter = None  # type: ignore # View instance to be destroyed -type can be inconsistent

    def set_image_rotation_angle(self) -> None:
        """Set the image rotation angle which will be read in by the presenter"""
        if self.rotate_angles_group.checkedAction().text() == "0°":
            if "Rotate Stack" in self.filter_params:
                del self.filter_params["Rotate Stack"]
        else:
            image_rotation_angle = int(self.rotate_angles_group.checkedAction().text().replace('°', ''))
            self.filter_params["Rotate Stack"] = {"params": {"angle": image_rotation_angle}}
        self.presenter.update_image_operation()

    def set_load_as_dataset_enabled(self, enabled: bool):
        self.load_as_dataset_action.setEnabled(enabled)

    def set_spectrum_visibility(self):
        widget_height = self.frameGeometry().height()
        if self.spectrum_action.isChecked():
            if not self.live_viewer.roi_object:
                self.live_viewer.add_roi()
            self.live_viewer.set_roi_visibility_flags(True)
            self.splitter.setSizes([int(0.7 * widget_height), int(0.3 * widget_height)])
            self.presenter.model.roi = self.live_viewer.get_roi()
            print(f"{self.presenter.model.roi.right=}")
            self.presenter.model.calc_mean_fully()
            self.presenter.update_spectrum(self.presenter.model.mean)
        else:
            self.live_viewer.set_roi_visibility_flags(False)
            self.splitter.setSizes([widget_height, 0])

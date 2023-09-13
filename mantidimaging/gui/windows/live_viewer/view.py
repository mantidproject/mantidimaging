# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QVBoxLayout

from mantidimaging.gui.mvp_base import BaseMainWindowView
from .live_view_widget import LiveViewWidget
from .presenter import LiveViewerWindowPresenter

import numpy as np

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover


class LiveViewerWindowView(BaseMainWindowView):
    """
    Live Viewer window view class.
    This class is responsible for handling user interaction with the window.
    """

    imageLayout: QVBoxLayout

    def __init__(self, main_window: 'MainWindowView', live_dir_path: Path) -> None:
        super().__init__(main_window, 'gui/ui/live_viewer_window.ui')
        self.setWindowTitle("Mantid Imaging - Live Viewer")
        self.main_window = main_window
        self.path = live_dir_path
        self.presenter = LiveViewerWindowPresenter(self, main_window)
        self.live_viewer = LiveViewWidget()
        self.imageLayout.addWidget(self.live_viewer)

    def show(self) -> None:
        """Show the window"""
        super().show()
        self.activateWindow()
        self.watch_directory()

        self.live_viewer.z_slider.valueChanged.connect(self.presenter.select_image)
        self.presenter.model.get_images()

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

    def set_image_index(self, index: int) -> None:
        self.live_viewer.z_slider.set_value(index)

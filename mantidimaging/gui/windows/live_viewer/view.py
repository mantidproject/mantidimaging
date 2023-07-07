# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PyQt5.QtWidgets import QVBoxLayout
from tifffile import tifffile

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
        self.show_first_image()

    def show_first_image(self):
        """Show the first image in the selected directory."""
        for file in self.path.iterdir():
            if file.suffix == ".tif" or file.suffix == ".tiff":
                self.image = tifffile.imread(file)
                break
        self.live_viewer.show_image(self.image)

    def set_image(self, image_data: Optional['np.ndarray'], autoLevels: bool = True):
        self.spectrum.image.setImage(image_data, autoLevels=autoLevels)

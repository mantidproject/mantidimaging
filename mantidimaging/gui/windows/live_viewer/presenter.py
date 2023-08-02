# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger
from tifffile import tifffile
from pathlib import Path

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.live_viewer.model import LiveViewerWindowModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover

logger = getLogger(__name__)


class LiveViewerWindowPresenter(BasePresenter):
    """
    The presenter for the Live Viewer window.

    This presenter is responsible for handling user interaction with the view and
    updating the model and view accordingly to look after the state of the window.
    """
    view: LiveViewerWindowView
    model: LiveViewerWindowModel

    def __init__(self, view: LiveViewerWindowView, main_window: MainWindowView):
        super().__init__(view)

        self.view = view
        self.main_window = main_window
        self.model = LiveViewerWindowModel(self)

    def set_dataset_path(self, path):
        """Set the path to the dataset."""
        self.model.path = path

    def update_image(self, image_path: str):
        """Update the image in the view."""
        if not Path(image_path).exists():
            return
        try:
            logger.debug("Showing image in presenter: %s", image_path)
            with tifffile.TiffFile(image_path) as tif:
                image_data = tif.asarray()
                self.view.show_image(image_data)
        except IOError as error:
            logger.error("Error reading image: %s", error)
            return

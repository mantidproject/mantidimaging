# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger
from tifffile import tifffile

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

    def clear_label(self):
        """Clear the label."""
        self.view.label_active_filename.setText("")

    def handle_deleted(self):
        """Handle the deletion of the image."""
        self.view.remove_image()
        self.clear_label()

    def update_image(self, images_list: list):
        """Update the image in the view."""
        if not images_list:
            self.view.remove_image()
            return
        try:
            with tifffile.TiffFile(images_list[-1].image_path) as tif:
                image_data = tif.asarray()
        except IOError as error:
            logger.error("Error reading image: %s", error)
            return
        except KeyError as key_error:
            logger.error("Error reading image: %s", key_error)
            return
        except ValueError as value_error:
            logger.error("Error reading image: %s", value_error)
            return

        self.view.show_most_recent_image(image_data)
        self.view.label_active_filename.setText(images_list[-1].image_name)

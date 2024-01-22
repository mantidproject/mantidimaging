# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from logging import getLogger
import numpy as np

from imagecodecs._deflate import DeflateError
from tifffile import tifffile, TiffFileError
from astropy.io import fits

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.live_viewer.model import LiveViewerWindowModel, Image_Data
from mantidimaging.core.operations.rotate_stack import RotateFilter
from mantidimaging.core.data import ImageStack

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
        self.selected_image: Image_Data | None = None

    def close(self) -> None:
        """Close the window."""
        self.model.close()
        self.model = None  # type: ignore # Presenter instance to be destroyed -type can be inconsistent
        self.view = None  # type: ignore # Presenter instance to be destroyed -type can be inconsistent

    def set_dataset_path(self, path: Path) -> None:
        """Set the path to the dataset."""
        self.model.path = path

    def clear_label(self) -> None:
        """Clear the label."""
        self.view.label_active_filename.setText("")

    def handle_deleted(self) -> None:
        """Handle the deletion of the image."""
        self.view.remove_image()
        self.clear_label()
        self.view.live_viewer.z_slider.set_range(0, 1)
        self.view.live_viewer.show_error(None)

    def update_image_list(self, images_list: list[Image_Data]) -> None:
        """Update the image in the view."""
        if not images_list:
            self.handle_deleted()
            return

        self.view.set_image_range((0, len(images_list) - 1))
        self.view.set_image_index(len(images_list) - 1)

    def select_image(self, index: int) -> None:
        if not self.model.images:
            return
        self.selected_image = self.model.images[index]
        self.view.label_active_filename.setText(self.selected_image.image_name)

        self.load_and_display_image(self.selected_image.image_path)

    def load_and_display_image(self, image_path: Path):
        try:
            if image_path.suffix.lower() in [".tif", ".tiff"]:
                with tifffile.TiffFile(image_path) as tif:
                    image_data = tif.asarray()
            elif image_path.suffix.lower() == ".fits":
                with fits.open(image_path.__str__()) as fit:
                    image_data = fit[0].data

            image_data = self.rotate_image(image_data, 90)
        except (IOError, KeyError, ValueError, TiffFileError, DeflateError) as error:
            message = f"{type(error).__name__} reading image: {image_path}: {error}"
            logger.error(message)
            self.view.remove_image()
            self.view.live_viewer.show_error(message)
            return
        if image_data.size == 0:
            message = "reading image: {image_path}: Image has zero size"
            logger.error("reading image: %s: Image has zero size", image_path)
            self.view.remove_image()
            self.view.live_viewer.show_error(message)
            return

        self.view.show_most_recent_image(image_data)
        self.view.live_viewer.show_error(None)

    def update_image_modified(self, image_path: Path):
        """
        Update the displayed image when the file is modified
        """
        if self.selected_image and image_path == self.selected_image.image_path:
            self.load_and_display_image(image_path)

    def rotate_image(self, image_data, ang: int):
        image_data_shape = image_data.shape
        image_data_temp = np.zeros(shape=(1, image_data_shape[0], image_data_shape[1]))
        image_data_temp[0] = image_data
        image_stack_temp = ImageStack(image_data_temp)
        rotated_imaged = RotateFilter().filter_func(image_stack_temp, angle=ang)
        return rotated_imaged.data[0].astype(int)

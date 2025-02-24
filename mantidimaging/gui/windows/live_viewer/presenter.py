# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from collections.abc import Callable
from logging import getLogger
import numpy as np
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer
from astropy.io import fits
from astropy.utils.exceptions import AstropyUserWarning

from imagecodecs._deflate import DeflateError
from tifffile import tifffile
from tifffile.tifffile import TiffFileError

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.live_viewer.model import LiveViewerWindowModel, Image_Data
from mantidimaging.core.operations.loader import load_filter_packages
from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.custom_exceptions import ImageLoadFailError

if TYPE_CHECKING:
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover

logger = getLogger(__name__)

IMAGE_lIST_UPDATE_TIME = 100


class Worker(QObject):
    finished = pyqtSignal()

    def __init__(self, presenter: LiveViewerWindowPresenter):
        super().__init__()
        self.presenter = presenter

    def run(self):
        self.presenter.model.calc_mean_chunk(100)
        self.finished.emit()


class LiveViewerWindowPresenter(BasePresenter):
    """
    The presenter for the Live Viewer window.

    This presenter is responsible for handling user interaction with the view and
    updating the model and view accordingly to look after the state of the window.
    """
    view: LiveViewerWindowView
    model: LiveViewerWindowModel
    op_func: Callable
    thread: QThread
    worker: Worker
    old_image_list_paths: list[Path] = []

    def __init__(self, view: LiveViewerWindowView, main_window: MainWindowView):
        super().__init__(view)

        self.view = view
        self.main_window = main_window
        self.model = LiveViewerWindowModel(self)
        self.selected_image: Image_Data | None = None
        self.filters = {f.filter_name: f for f in load_filter_packages()}

        self.handle_roi_change_timer = QTimer()
        self.handle_roi_change_timer.setSingleShot(True)
        self.handle_roi_change_timer.timeout.connect(self.handle_roi_moved)

        self.update_image_list_timer = QTimer()
        self.update_image_list_timer.setSingleShot(True)
        self.update_image_list_timer.timeout.connect(self.update_image_list)

        self.model.image_cache.use_loading_function(self.load_image_from_path)

    def close(self) -> None:
        """Close the window."""
        if self.model is not None:
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

    def update_image_list(self) -> None:
        """Update the image in the view."""
        images_list = self.model.images
        if not images_list:
            self.handle_deleted()
            self.view.set_load_as_dataset_enabled(False)
            self.model.clear_mean_partial()
            self.update_intensity_with_mean()
        else:
            if self.view.intensity_action.isChecked():
                if not self.view.live_viewer.roi_object:
                    self.view.live_viewer.add_roi()
                self.model.roi = self.view.live_viewer.get_roi()
                images_list_paths = [image.image_path for image in images_list]
                if self.old_image_list_paths == images_list_paths[:-1]:
                    self.try_add_mean(images_list[-1])
                    self.update_intensity(self.model.mean)
                    self.old_image_list_paths = images_list_paths
                else:
                    self.model.clear_mean_partial()
                    self.run_mean_chunk_calc()
            self.view.set_image_range((0, len(images_list) - 1))
            self.view.set_image_index(len(images_list) - 1)
            self.view.set_load_as_dataset_enabled(True)

    def notify_update_image_list(self) -> None:
        self.update_image_list_timer.start(IMAGE_lIST_UPDATE_TIME)

    def try_add_mean(self, image: Image_Data) -> None:
        try:
            image_data = self.model.image_cache.load_image(image)
            self.model.add_mean(image.image_path, image_data)
            self.update_intensity_with_mean()
        except ImageLoadFailError as error:
            logger.error(error.message)
            self.model.add_mean(image.image_path, None)

    def select_image(self, index: int) -> None:
        if not self.model.images:
            return
        self.selected_image = self.model.images[index]
        if not self.selected_image:
            return
        image_timestamp = self.selected_image.image_modified_time_stamp
        self.view.label_active_filename.setText(f"{self.selected_image.image_name} - {image_timestamp}")

        self.display_image(self.selected_image)

    def display_image(self, image_data_obj: Image_Data) -> None:
        """
        Display image in the view after validating contents
        """
        try:
            image_data = self.model.image_cache.load_image(image_data_obj)
        except ImageLoadFailError as error:
            if not error.is_logged():
                logger.error(error.message)
            self.view.remove_image()
            self.view.live_viewer.show_error(error.message)
            return
        image_data = self.perform_operations(image_data)
        if image_data.size == 0:
            message = "reading image: {image_path}: Image has zero size"
            logger.error("reading image: %s: Image has zero size", image_data_obj.image_path)
            self.view.remove_image()
            self.view.live_viewer.show_error(message)
            return
        self.view.show_most_recent_image(image_data)
        self.view.live_viewer.show_error(None)

    @staticmethod
    def load_image_from_path(image_path: Path) -> np.ndarray:
        """
        Load a .Tif, .Tiff or .Fits file only if it exists
        and returns as an ndarray
        """
        if image_path.suffix.lower() in [".tif", ".tiff"]:
            try:
                with tifffile.TiffFile(image_path) as tif:
                    image_data = tif.asarray()
                return image_data
            except (OSError, KeyError, ValueError, TiffFileError, DeflateError) as err:
                raise ImageLoadFailError(image_path, err) from err
        elif image_path.suffix.lower() == ".fits":
            try:
                with fits.open(image_path) as fits_hdul:
                    image_data = fits_hdul[0].data
                return image_data
            except (OSError, TypeError, ValueError, AstropyUserWarning) as err:
                raise ImageLoadFailError(image_path, err) from err
        else:
            raise ImageLoadFailError(image_path,
                                     source_error=FileNotFoundError,
                                     message=f"Unsupported file type: {image_path.suffix}")

    def update_image_modified(self, image_path: Path) -> None:
        """
        Update the displayed image when the file is modified
        """
        if self.selected_image and image_path == self.selected_image.image_path:
            self.display_image(self.selected_image)
            self.try_add_mean(self.selected_image)
            self.update_intensity_with_mean()

    def update_image_operation(self) -> None:
        """
        Reload the current image if an operation has been performed on the current image
        """
        if self.selected_image is not None:
            self.display_image(self.selected_image)

    def convert_image_to_imagestack(self, image_data) -> ImageStack:
        """
        Convert the single image to an imagestack so the Operations framework can be used
        """
        image_data_shape = image_data.shape
        image_data_temp = np.zeros(shape=(1, image_data_shape[0], image_data_shape[1]))
        image_data_temp[0] = image_data
        return ImageStack(image_data_temp)

    def perform_operations(self, image_data) -> np.ndarray:
        if not self.view.filter_params:
            return image_data
        image_stack = self.convert_image_to_imagestack(image_data)
        for operation in self.view.filter_params:
            op_class = self.filters[operation]
            op_func = op_class.filter_func
            op_params = self.view.filter_params[operation]["params"]
            op_func(image_stack, **op_params)
        return image_stack.slice_as_array(0)[0]

    def load_as_dataset(self) -> None:
        if self.model.images:
            image_dir = self.model.images[0].image_path.parent
            self.main_window.show_image_load_dialog_with_path(str(image_dir))

    def update_intensity(self, spec_data: list | np.ndarray) -> None:
        self.view.intensity_profile.clearPlots()
        self.view.intensity_profile.plot(spec_data)

    def handle_roi_moved(self) -> None:
        roi = self.view.live_viewer.get_roi()
        if roi != self.model.roi:
            self.model.clear_mean_partial()
        self.model.roi = roi
        self.set_roi_enabled(False)
        self.run_mean_chunk_calc()

    def run_mean_chunk_calc(self) -> None:
        self.thread = QThread()
        self.worker = Worker(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.thread_cleanup)
        self.thread.start()

    def thread_cleanup(self) -> None:
        self.update_intensity_with_mean()
        self.set_roi_enabled(True)
        if np.isnan(self.model.mean).any() and self.model.mean_readable.all():
            self.try_next_mean_chunk()
        if not np.isnan(self.model.mean * self.model.mean_readable).any():
            self.try_next_mean_chunk()

    def handle_notify_roi_moved(self) -> None:
        self.model.clear_mean_partial()
        if not self.handle_roi_change_timer.isActive():
            self.handle_roi_change_timer.start(10)

    def update_intensity_with_mean(self) -> None:
        self.view.intensity_profile.clearPlots()
        self.view.intensity_profile.plot(self.model.mean)

    def set_roi_enabled(self, enable: bool):
        if self.view.live_viewer.roi_object is not None:
            self.view.live_viewer.roi_object.blockSignals(not enable)

    def try_next_mean_chunk(self) -> None:
        if np.isnan(self.model.mean).any():
            if not self.handle_roi_change_timer.isActive():
                self.handle_roi_change_timer.start(10)

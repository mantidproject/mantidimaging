# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import time
from typing import TYPE_CHECKING
from pathlib import Path
from logging import getLogger

import numpy as np
from PyQt5.QtCore import QFileSystemWatcher, QObject, pyqtSignal, QTimer

from tifffile import tifffile
from astropy.io import fits

from mantidimaging.core.utility import ExecutionProfiler
from mantidimaging.core.utility.sensible_roi import SensibleROI

if TYPE_CHECKING:
    from os import stat_result
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowPresenter

LOG = getLogger(__name__)


class ImageCache:
    """
    An ImageCache class to be used as a decorator on image read functions to store recent images in memory
    """
    cache_dict: dict = {}
    image_list: list[Image_Data]
    image_paths: set[str] = set()
    mean: np.ndarray = np.array([])
    roi: SensibleROI | None = None
    param_to_calc: list[str] = []
    max_cache_size: int = 100
    buffer_size: int = 10

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        #print(f"Arguments: {args}, Keyword Arguments: {kwargs}")
        result = self.func(*args, **kwargs)
        self.add_to_cache(args, result)
        return result

    def add_to_cache(self, args, image_array: np.ndarray):
        if args not in self.cache_dict.keys():
            self.cache_dict[args] = image_array

    def remove_from_cache(self, image: Image_Data):
        if image.image_path in self.cache_dict.keys():
            del self.cache_dict[image.image_path]

    # def update_param_calculations(self) -> None:
    #     if 'mean' in self.param_to_calc:
    #         if len(self.mean) == len(self.image_list) - 1:
    #             self.add_last_mean()
    #         else:
    #             if self.roi:
    #                 self.calc_mean_fully_roi()
    #             else:
    #                 self.calc_mean_fully()
    #
    # def add_last_mean(self) -> None:
    #     if self.delayed_stack is not None:
    #         if self.roi:
    #             left, top, right, bottom = self.roi
    #             mean_to_add = dask.optimize(dask.array.mean(self.delayed_stack[-1, top:bottom,
    #                                                                            left:right]))[0].compute()
    #         else:
    #             mean_to_add = dask.optimize(dask.array.mean(self.delayed_stack[-1]))[0].compute()
    #         self.mean = np.append(self.mean, mean_to_add)
    #         self.calc_mean_buffer()

    # def calc_mean_fully(self) -> None:
    #     if self.delayed_stack is not None:
    #         self.mean = dask.array.mean(self.delayed_stack, axis=(1, 2)).compute()
    #
    # def calc_mean_fully_roi(self):
    #     if self.delayed_stack is not None and self.image_list:
    #         left, top, right, bottom = self.roi
    #         current_cache_size = len(self.)
    #         self.mean = np.full(len(self.image_list), np.nan)
    #         np.put(self.mean, range(-current_cache_size, 0), self.calc_mean_cached_images(left, top, right, bottom))
    #
    # def calc_mean_cached_images(self, left, top, right, bottom):
    #     current_cache_size = self.get_computed_image.cache_info()[3]
    #     cache_stack = [
    #         self.get_computed_image(index)
    #         for index in range(self.selected_index - current_cache_size + 1, self.selected_index + 1, 1)
    #     ]
    #     cache_stack_array = np.stack(cache_stack)
    #     cache_stack_mean = np.mean(cache_stack_array[:, top:bottom, left:right], axis=(1, 2))
    #     return cache_stack_mean
    #
    # def calc_mean_buffer(self):
    #     nanInds = np.argwhere(np.isnan(self.mean))
    #     left, top, right, bottom = self.roi
    #     if nanInds.size > 0:
    #         print(f"{self.mean=}")
    #         if nanInds.size < self.buffer_size:
    #             buffer_start = 0
    #         else:
    #             buffer_start = nanInds.size - self.buffer_size
    #         dask_mean = dask.optimize(
    #             dask.array.mean(self.delayed_stack[buffer_start:nanInds.size, top:bottom, left:right],
    #                             axis=(1, 2)))[0].compute()
    #         np.put(self.mean, range(buffer_start, nanInds.size), dask_mean)

    def delete_all_data(self):
        pass

    def add_param_to_calc(self, param_name: str):
        self.param_to_calc.append(param_name)


class Image_Data:
    """
    Image Data Class to store represent image data.

    ...

    Attributes
    ----------
    image_path : Path
        path to image file
    image_name : str
        name of image file
    image_size : int
        size of image file
    image_modified_time : float
        last modified time of image file
    """

    def __init__(self, image_path: Path):
        """
        Constructor for Image_Data class.

        Parameters
        ----------
        image_path : str
            path to image file
        """
        self.image_path = image_path
        self.image_name = image_path.name
        self._stat = image_path.stat()

    @property
    def stat(self) -> stat_result:
        return self._stat

    @property
    def image_modified_time(self) -> float:
        """Return the image modified time"""
        return self._stat.st_mtime

    @property
    def image_modified_time_stamp(self) -> str:
        """Return the image modified time as a string"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.image_modified_time))


class SubDirectory:

    def __init__(self, path: Path) -> None:
        self.path = path
        self._stat = path.stat()
        self.mtime = self._stat.st_mtime

    @property
    def modification_time(self) -> float:
        return self.mtime


class LiveViewerWindowModel:
    """
    The model for the spectrum viewer window.

    ...

    Attributes
    ----------
    presenter : LiveViewerWindowPresenter
        presenter for the spectrum viewer window
    path : Path
        path to dataset
    images : list
        list of images in directory
    """

    def __init__(self, presenter: LiveViewerWindowPresenter):
        """
        Constructor for LiveViewerWindowModel class.

        Parameters
        ----------
        presenter : LiveViewerWindowPresenter
            presenter for the spectrum viewer window
        """

        self.presenter = presenter
        self._dataset_path: Path | None = None
        self.image_watcher: ImageWatcher | None = None
        self._images: list[Image_Data] = []
        self.mean: np.array = np.array([])
        self.mean_dict: dict[Path, float] = {}
        self.roi: SensibleROI | None = None

    @property
    def path(self) -> Path | None:
        return self._dataset_path

    @path.setter
    def path(self, path: Path) -> None:
        self._dataset_path = path
        self.image_watcher = ImageWatcher(path)
        self.image_watcher.image_changed.connect(self._handle_image_changed_in_list)
        self.image_watcher.recent_image_changed.connect(self.handle_image_modified)
        self.image_watcher._handle_notified_of_directry_change(str(path))

    @property
    def images(self):
        return self._images if self._images is not None else None

    @images.setter
    def images(self, images):
        self._images = images

    def set_roi(self, roi: SensibleROI):
        self.roi = roi

    def _handle_image_changed_in_list(self, image_files: list[Image_Data]) -> None:
        """
        Handle an image changed event. Update the image in the view.
        This method is called when the image_watcher detects a change
        which could be a new image, edited image or deleted image.

        :param image_files: list of image files
        """
        self.images = image_files
        # if dask_image_stack.image_list:
        #     self.image_stack = dask_image_stack
        self.presenter.update_image_list(image_files)

    def handle_image_modified(self, image_path: Path):
        self.presenter.update_image_modified(image_path)

    def close(self) -> None:
        """Close the model."""
        if self.image_watcher:
            self.image_watcher.remove_path()
            self.image_watcher = None
        self.presenter = None  # type: ignore # Model instance to be destroyed -type can be inconsistent

    def add_mean(self, image_data_obj: Image_Data, image_array: np.array) -> None:
        if self.roi:
            left, top, right, bottom = self.roi
            mean_to_add = np.mean(image_array[top:bottom, left:right])
        else:
            mean_to_add = np.mean(image_array)
        self.mean_dict[image_data_obj.image_path] = mean_to_add
        self.mean = list(self.mean_dict.values())

    def clear_mean(self):
        self.mean_dict.clear()

    def calc_mean_fully(self) -> None:
        for image in self.images:
            self.add_mean(image, self.load_image_from_path(image.image_path))

    @staticmethod
    def load_image_from_path(image_path: Path) -> np.ndarray:
        """
        Load a .Tif, .Tiff or .Fits file only if it exists
        and returns as an ndarray
        """
        if image_path.suffix.lower() in [".tif", ".tiff"]:
            with tifffile.TiffFile(image_path) as tif:
                image_data = tif.asarray()
        elif image_path.suffix.lower() == ".fits":
            with fits.open(image_path.__str__()) as fit:
                image_data = fit[0].data
        return image_data

class ImageWatcher(QObject):
    """
    A class to watch a directory for new images.

    ...

    Attributes
    ----------
    directory : Path
        path to directory to watch
    watcher : QFileSystemWatcher
        file system watcher to watch directory
    image_changed : pyqtSignal
        signal emitted when an image is added or removed

    Methods
    -------
    find_images()
        Find all the images in the directory
    sort_images_by_modified_time(images)
        Sort the images by modified time.
    """
    image_changed = pyqtSignal(list)  # Signal emitted when an image is added or removed
    update_spectrum = pyqtSignal(np.ndarray)  # Signal emitted to update the Live Viewer Spectrum
    recent_image_changed = pyqtSignal(Path)
    create_delayed_array: bool = False

    def __init__(self, directory: Path):
        """
        Constructor for ImageWatcher class which inherits from QObject.

        Parameters
        ----------
        directory : Path
            path to directory to watch
        """

        super().__init__()
        self.directory = directory
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self._handle_notified_of_directry_change)
        self.handle_change_timer = QTimer(self)
        self.handle_change_timer.setSingleShot(True)
        self.handle_change_timer.timeout.connect(self._handle_directory_change)
        self.changed_directory = directory

        self.recent_file_watcher = QFileSystemWatcher()
        self.recent_file_watcher.fileChanged.connect(self.handle_image_modified)

        self.sub_directories: dict[Path, SubDirectory] = {}
        self.add_sub_directory(SubDirectory(self.directory))

    def find_images(self, directory: Path) -> list[Image_Data]:
        """
        Find all the images in the directory.
        """
        image_files = []
        for file_path in directory.iterdir():
            if self._is_image_file(file_path.name):
                try:
                    image_obj = Image_Data(file_path)
                    image_files.append(image_obj)
                except FileNotFoundError:
                    continue

        return image_files

    def find_sub_directories(self, directory: Path) -> None:
        # COMPAT python < 3.12 - Can replace with Path.walk()
        try:
            for filename in directory.glob("**/*"):
                if filename.is_dir():
                    self.add_sub_directory(SubDirectory(filename))
        except FileNotFoundError:
            pass

    def sort_sub_directory_by_modified_time(self) -> None:
        self.sub_directories = dict(
            sorted(self.sub_directories.items(), key=lambda p: p[1].modification_time, reverse=True))

    @staticmethod
    def sort_images_by_modified_time(images: list[Image_Data]) -> list[Image_Data]:
        """
        Sort the images by modified time.

        :param images: list of image objects to sort by modified time
        :return: sorted list of images
        """
        return sorted(images, key=lambda x: x.image_modified_time)

    def _handle_notified_of_directry_change(self, directory: str) -> None:
        """
        Quickly handle the notification event for a change, and start the timer if needed. If files are arriving faster
        than _handle_directory_change() can process them, we don't end up with a queue of work to do. The timeout is set
        small so that we can pull multiple notification off the queue and then run _handle_directory_change() once.
        """
        self.changed_directory = Path(directory)
        if not self.handle_change_timer.isActive():
            self.handle_change_timer.start(10)

    def _handle_directory_change(self) -> None:
        """
        Handle a directory change event. Update the list of images
        to reflect directory changes and emit the image_changed signal
        with the sorted image list.
        """
        directory_path = self.changed_directory

        # Force the modification time of signal directory, because file changes may not update
        # parent dir mtime
        if directory_path.exists():
            this_dir = SubDirectory(directory_path)
            this_dir.mtime = time.time()
            self.add_sub_directory(this_dir)

        self.clear_deleted_sub_directories(directory_path)
        if not self.sub_directories:
            raise FileNotFoundError(f"Live directory not found: {self.directory}"
                                    "\nHas it been deleted?")
        self.find_sub_directories(directory_path)
        self.sort_sub_directory_by_modified_time()

        for newest_directory in self.sub_directories.values():
            try:
                images = self.find_images(newest_directory.path)
            except FileNotFoundError:
                images = []

            if len(images) > 0:
                break
        images = self.sort_images_by_modified_time(images)
        self.update_recent_watcher(images[-1:])
        self.image_changed.emit(images)

    @staticmethod
    def _is_image_file(file_name: str) -> bool:
        """
        Check if a file is an tiff or tif image file.

        :param file_name: name of file
        :return: True if file is an image file
        """
        image_extensions = ('tif', 'tiff', 'fits')
        return file_name.rpartition(".")[2].lower() in image_extensions

    def remove_path(self) -> None:
        """
        Remove the currently set path
        """
        self.watcher.removePaths([str(path) for path in self.sub_directories.keys()])
        self.recent_file_watcher.removePaths(self.recent_file_watcher.files())
        assert len(self.watcher.files()) == 0
        assert len(self.watcher.directories()) == 0
        assert len(self.recent_file_watcher.files()) == 0
        assert len(self.recent_file_watcher.directories()) == 0

    def update_recent_watcher(self, images: list[Image_Data]) -> None:
        self.recent_file_watcher.removePaths(self.recent_file_watcher.files())
        self.recent_file_watcher.addPaths([str(image.image_path) for image in images])

    def handle_image_modified(self, file_path) -> None:
        self.recent_image_changed.emit(Path(file_path))

    def add_sub_directory(self, sub_dir: SubDirectory) -> None:
        if sub_dir.path not in self.sub_directories:
            self.watcher.addPath(str(sub_dir.path))

        self.sub_directories[sub_dir.path] = sub_dir

    def remove_sub_directory(self, sub_dir: Path) -> None:
        if sub_dir in self.sub_directories:
            self.watcher.removePath(str(sub_dir))

        del self.sub_directories[sub_dir]

    def clear_deleted_sub_directories(self, directory: Path) -> None:
        for sub_dir in list(self.sub_directories):
            if sub_dir.is_relative_to(directory) and not sub_dir.exists():
                self.remove_sub_directory(sub_dir)

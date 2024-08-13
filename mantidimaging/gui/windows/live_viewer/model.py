# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import time
from typing import TYPE_CHECKING
from pathlib import Path
from logging import getLogger

import dask.array
from PyQt5.QtCore import QFileSystemWatcher, QObject, pyqtSignal, QTimer

import dask_image.imread
from astropy.io import fits

if TYPE_CHECKING:
    from os import stat_result
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowPresenter

LOG = getLogger(__name__)


class DaskImageDataStack:
    """
    A Dask Image Data Stack Class to hold a delayed array of all the images in the Live Viewer Path
    """
    delayed_stack: dask.array.Array | None = None
    image_list: list[Image_Data]
    create_delayed_array: bool

    def __init__(self, image_list: list[Image_Data], create_delayed_array: bool = True):
        self.image_list = image_list

        if image_list and create_delayed_array:
            arrays = self.get_delayed_arrays()
            if arrays:
                if image_list[0].image_path.suffix.lower() in [".tif", ".tiff"]:
                    self.delayed_stack = dask.array.stack(dask.array.array(arrays))
                elif image_list[0].image_path.suffix.lower() in [".fits"]:
                    with fits.open(image_list[0].image_path.__str__()) as fit:
                        sample = fit[0].data
                    lazy_arrays = [dask.array.from_delayed(x, shape=sample.shape, dtype=sample.dtype) for x in arrays]
                    self.delayed_stack = dask.array.stack(lazy_arrays)

    @property
    def shape(self):
        return self.delayed_stack.shape

    def get_delayed_arrays(self) -> list[dask.array.Array] | None:
        if self.image_list[0].image_path.suffix.lower() in [".tif", ".tiff"]:
            return [dask_image.imread.imread(image_data.image_path)[0] for image_data in self.image_list]
        elif self.image_list[0].image_path.suffix.lower() == ".fits":
            return [dask.delayed(fits.open)(image_data.image_path)[0].data for image_data in self.image_list]
        else:
            return None

    def get_delayed_image(self, index: int) -> dask.array.Array | None:
        return self.delayed_stack[index] if self.delayed_stack else None

    def get_image_data(self, index: int) -> Image_Data | None:
        return self.image_list[index] if self.image_list else None


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
    delayed_array: dask.array.Array
        A delayed dask array of the image data
    """
    delayed_array: dask.array.Array
    create_delayed_array: bool

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
        self.images: list[Image_Data] = []
        self.image_stack: DaskImageDataStack

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

    def _handle_image_changed_in_list(self, image_files: list[Image_Data],
                                      dask_image_stack: DaskImageDataStack) -> None:
        """
        Handle an image changed event. Update the image in the view.
        This method is called when the image_watcher detects a change
        which could be a new image, edited image or deleted image.

        :param image_files: list of image files
        """
        self.images = image_files
        self.image_stack = dask_image_stack
        self.presenter.update_image_list(image_files)

    def handle_image_modified(self, image_path: Path):
        self.presenter.update_image_modified(image_path)

    def close(self) -> None:
        """Close the model."""
        if self.image_watcher:
            self.image_watcher.remove_path()
            self.image_watcher = None
        self.presenter = None  # type: ignore # Model instance to be destroyed -type can be inconsistent


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
    image_changed = pyqtSignal(list, DaskImageDataStack)  # Signal emitted when an image is added or removed
    recent_image_changed = pyqtSignal(Path)
    create_delayed_array: bool = True

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
        dask_image_stack = DaskImageDataStack(images, create_delayed_array=self.create_delayed_array)
        self.update_recent_watcher(images[-1:])
        self.image_changed.emit(images, dask_image_stack)

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

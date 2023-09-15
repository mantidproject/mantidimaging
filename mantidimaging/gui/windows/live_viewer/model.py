# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path
from logging import getLogger
from PyQt5.QtCore import QFileSystemWatcher, QObject, pyqtSignal

if TYPE_CHECKING:
    from os import stat_result
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowPresenter

LOG = getLogger(__name__)


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
    def image_size(self) -> int:
        """Return the image size"""
        return self._stat.st_size

    @property
    def image_modified_time(self) -> float:
        """Return the image modified time"""
        return self._stat.st_mtime


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

    def __init__(self, presenter: 'LiveViewerWindowPresenter'):
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

    @property
    def path(self) -> Path | None:
        return self._dataset_path

    @path.setter
    def path(self, path: Path) -> None:
        self._dataset_path = path
        self.image_watcher = ImageWatcher(path)
        self.image_watcher.image_changed.connect(self._handle_image_changed_in_list)
        self.image_watcher._handle_directory_change("")

    def _handle_image_changed_in_list(self, image_files: list[Image_Data]) -> None:
        """
        Handle an image changed event. Update the image in the view.
        This method is called when the image_watcher detects a change
        which could be a new image, edited image or deleted image.

        :param image_files: list of image files
        """
        self.images = image_files
        self.presenter.update_image_list(image_files)

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
    image_changed = pyqtSignal(list)  # Signal emitted when an image is added or removed

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
        self.watcher.directoryChanged.connect(self._handle_directory_change)
        self.watcher.addPath(str(self.directory))

    def find_images(self) -> list[Image_Data]:
        """
        Find all the images in the directory.
        """
        image_files = []
        for file_path in Path(self.directory).iterdir():
            if self._is_image_file(file_path.name):
                try:
                    image_obj = Image_Data(file_path)
                    if image_obj.image_size > 45:
                        image_files.append(image_obj)
                except FileNotFoundError:
                    continue

        return image_files

    @staticmethod
    def sort_images_by_modified_time(images: list[Image_Data]) -> list[Image_Data]:
        """
        Sort the images by modified time.

        :param images: list of image objects to sort by modified time
        :return: sorted list of images
        """
        return sorted(images, key=lambda x: x.image_modified_time)

    def _handle_directory_change(self, directory: str) -> None:
        """
        Handle a directory change event. Update the list of images
        to reflect directory changes and emit the image_changed signal
        with the sorted image list.

        :param directory: directory that has changed
        """

        images = self.find_images()
        images = self.sort_images_by_modified_time(images)
        self.image_changed.emit(images)

    @staticmethod
    def _is_image_file(file_name: str) -> bool:
        """
        Check if a file is an tiff or tif image file.

        :param file_name: name of file
        :return: True if file is an image file
        """
        image_extensions = ['.tif', '.tiff']
        file_names = any(file_name.lower().endswith(ext) for ext in image_extensions)
        return file_names

    def remove_path(self):
        """
        Remove the currently set path
        """
        self.watcher.removePath(str(self.directory))

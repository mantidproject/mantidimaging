# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
from logging import getLogger
from PyQt5.QtCore import QFileSystemWatcher, QObject, pyqtSignal

if TYPE_CHECKING:
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowPresenter

LOG = getLogger(__name__)


class Image_Data:
    """
    Image Data Class to store represent image data.

    ...

    Attributes
    ----------
    image_path : str
        path to image file
    image_name : str
        name of image file
    image_size : int
        size of image file
    image_modified_time : int
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
    def stat(self):
        return self._stat

    @property
    def image_size(self):
        """Return the image size"""
        return self._stat.st_size

    @property
    def image_modified_time(self):
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
    path : str
        path to dataset
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
        self._dataset_path = None

    @property
    def path(self):
        return self._dataset_path

    @path.setter
    def path(self, path):
        self._dataset_path = path
        self.image_watcher = ImageWatcher(self.path)
        self.image_watcher.image_changed.connect(self._handle_image_changed_in_list)
        self.image_watcher.find_images()
        self.image_watcher.get_images()

    def _handle_image_changed_in_list(self, image_files: list[Image_Data]) -> None:
        """
        Handle an image changed event. Update the image in the view.
        This method is called when the image_watcher detects a change
        which could be a new image, edited image or deleted image.

        :param image_files: list of image files
        """
        if not image_files:
            self.presenter.handle_deleted()
            self.presenter.update_image([])
        else:
            self.presenter.update_image(image_files)


class ImageWatcher(QObject):
    """
    A class to watch a directory for new images.

    ...

    Attributes
    ----------
    directory : str
        path to directory to watch
    watcher : QFileSystemWatcher
        file system watcher to watch directory
    images : list
        list of images in directory
    image_changed : pyqtSignal
        signal emitted when an image is added or removed

    Methods
    -------
    find_images()
        Find all the images in the directory and emit the
        image_changed signal for the last modified image.
    sort_images_by_modified_time(images)
        Sort the images by modified time.
    find_last_modified_image()
        Find the last modified image in the directory and
        emit the image_changed signal.
    """
    image_changed = pyqtSignal(list)  # Signal emitted when an image is added or removed

    def __init__(self, directory):
        """
        Constructor for ImageWatcher class which inherits from QObject.

        Parameters
        ----------
        directory : str
            path to directory to watch
        """

        super().__init__()
        self.directory = directory
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self._handle_directory_change)
        self.watcher.addPath(str(self.directory))
        self.images = []

    def find_images(self) -> None:
        """
        Find all the images in the directory and emit the
        image_changed signal for the last modified image.
        """
        self.images = self._get_image_files()

    def sort_images_by_modified_time(self, images: list[Image_Data]) -> list[Image_Data]:
        """
        Sort the images by modified time.

        :param images: list of image objects to sort by modified time
        :return: sorted list of images
        """
        return sorted(images, key=lambda x: x.image_modified_time)

    def get_images(self):
        """Return the sorted images"""
        return self.images

    def _handle_directory_change(self, directory) -> None:
        """
        Handle a directory change event. Update the list of images
        to reflect directory changes and emit the image_changed signal
        for the last modified image.

        :param directory: directory that has changed
        """
        try:
            self.find_images()
            self.image_changed.emit(self.images)
        except FileNotFoundError:
            self.image_changed.emit([])

    def _get_image_files(self):
        image_files = []
        for file_path in Path(self.directory).iterdir():
            if self._is_image_file(file_path.name):
                try:
                    image_obj = Image_Data(file_path)
                    if image_obj.image_size > 45:
                        image_files.append(image_obj)
                except FileNotFoundError:
                    continue
        return self.sort_images_by_modified_time(image_files)

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

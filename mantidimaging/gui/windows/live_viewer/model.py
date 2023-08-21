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
        self.image_path: Path = image_path
        self.image_name: str = image_path.name
        self._image_size: int
        self._image_modified_time: float
        self._set_file_info()

    def _set_file_info(self):
        self.image_size = self.image_path
        self.image_modified_time = self.image_path

    @property
    def image_size(self):
        """Return the image size"""
        return self._image_size

    @image_size.setter
    def image_size(self, image_path: str):
        """
        assume image may be deleted before objet is fully created
        """
        try:
            self._image_size = Path(image_path).stat().st_size
        except FileNotFoundError:
            self._image_size = 0

    @property
    def image_modified_time(self):
        """Return the image modified time"""
        return self._image_modified_time

    @image_modified_time.setter
    def image_modified_time(self, image_path: str):
        """ Assume image may be deleted before object is fully created"""
        try:
            self._image_modified_time = Path(image_path).stat().st_mtime
        except FileNotFoundError:
            self._image_modified_time = 0


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
        self.image_watcher.image_changed.connect(self._handle_image_changed)
        self.image_watcher.find_images()
        self.image_watcher.find_last_modified_image()

    def _handle_image_changed(self, image_file) -> None:
        """
        Handle an image changed event. Update the image in the view.
        This method is called when the image_watcher detects a change
        which could be a new image, edited image or deleted image.

        :param image_file: path to image file
        """
        if image_file == '':
            self.presenter.handle_deleted()
        self.presenter.update_image(image_file)


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
    image_changed = pyqtSignal(str)  # Signal emitted when an image is added or removed

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

    def find_last_modified_image(self):
        """
        Find the last modified image in the directory and
        emit the image_changed signal.
        """

        if self.images:
            try:
                last_modified_image = self.images[-1].image_path
            except FileNotFoundError:
                last_modified_image = ''

            self.image_changed.emit(str(last_modified_image))

    def _handle_directory_change(self, directory) -> None:
        """
        Handle a directory change event. Update the list of images
        to reflect directory changes and emit the image_changed signal
        for the last modified image.

        :param directory: directory that has changed
        """
        self.find_images()
        try:
            last_image = self.images[-1].image_path
        except IndexError:
            last_image = ''
        self.image_changed.emit(str(last_image))

    def _validate_file(self, file_path) -> bool:
        """
        Check if a file is valid.

        :param file_path: path to file
        :return: True if file is valid as int (0 or 1)
        """
        return bool(file_path.is_file() and self._is_image_file(file_path.name))

    def _validate_images(self, images: list) -> bool:
        """
        Check if a list of images are valid.

        :param images: list of images
        :return: True if all images are valid
        """
        return all(self._validate_file(image) for image in images)

    def _get_image_files(self):
        image_files = []
        for file_path in Path(self.directory).iterdir():
            file_size = file_path.stat().st_size
            if file_size > 45 and self._validate_file(file_path):
                LOG.debug(f'VALID FILE: {file_path} is an image file and is not empty')
                image_files.append(Image_Data(file_path))
            else:
                LOG.debug(f'INVALID FILE: {file_path} is not valid an image file or is empty')
        sorted_images = self.sort_images_by_modified_time(image_files)
        return sorted_images

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

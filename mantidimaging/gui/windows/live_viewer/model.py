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


class LiveViewerWindowModel:
    """
    The model for the spectrum viewer window.
    """

    def __init__(self, presenter: 'LiveViewerWindowPresenter'):
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

    def _handle_image_changed(self, image_file):
        self.presenter.update_image(image_file)


class ImageWatcher(QObject):
    """
    A class to watch a directory for new images.
    """
    image_changed = pyqtSignal(str)  # Signal emitted when an image is added or removed

    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self._handle_directory_change)
        self.watcher.addPath(str(self.directory))
        self.images = []

    def find_images(self):
        """
        Find all the images in the directory and emit the
        image_changed signal for the last modified image.
        """
        self.images = self._get_image_files()

    def find_last_modified_image(self):
        """
        Find the last modified image in the directory and
        emit the image_changed signal.
        """
        if self.images:
            last_modified_image = max(self.images, key=lambda x: x.stat().st_mtime)
            self.image_changed.emit(str(last_modified_image))
            LOG.debug('Last modified image: %s', last_modified_image)

    def _handle_directory_change(self, directory):
        LOG.debug('Directory changed: %s', directory)
        self.find_images()
        self.find_last_modified_image()

    def _validate_file(self, file_path) -> bool:
        """
        Check if a file is valid.
        """
        return file_path.is_file() and self._is_image_file(file_path.name)

    def _get_image_files(self):
        image_files = []
        for file_path in Path(self.directory).iterdir():
            file_size = file_path.stat().st_size
            if file_size > 45 and self._validate_file(file_path):
                LOG.debug(f'VALID FILE: {file_path} is an image file and is not empty')
                image_files.append(file_path)
            else:
                LOG.debug(f'INVALID FILE: {file_path} is not valid an image file or is empty')
        return image_files

    @staticmethod
    def _is_image_file(file_name):
        image_extensions = ['.tif', '.tiff']
        file_names = any(file_name.lower().endswith(ext) for ext in image_extensions)
        return file_names

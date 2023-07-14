# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
from PyQt5.QtCore import QFileSystemWatcher, QObject, pyqtSignal

if TYPE_CHECKING:
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowPresenter


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
        self.watcher.fileChanged.connect(self._handle_file_change)
        self.watcher.addPath(str(self.directory))
        self.images = []

    def find_images(self):
        """
        Find all the images in the directory and emit the
        image_changed signal for the last modified image.
        """
        self.images = self._get_image_files()
        for image_file in self.images:
            self.image_changed.emit(str(image_file))

    def find_last_modified_image(self):
        """
        Find the last modified image in the directory and
        emit the image_changed signal.
        """
        if self.images:
            last_modified_image = max(self.images, key=lambda x: x.stat().st_mtime)
            self.image_changed.emit(str(last_modified_image))

    def _handle_directory_change(self, directory):
        self.find_images()
        self.find_last_modified_image()

    def _handle_file_change(self, file):
        file_path = Path(self.directory) / file
        if file_path in self.images:
            if file_path.exists():
                self.image_changed.emit(str(file_path))
            else:
                self.images.remove(file_path)
                if not self.images:
                    # If no images are left, emit image_removed signal
                    self.image_changed.emit(str(file_path))
                    print('No images left, removing last image')
                else:
                    # Find the last modified image after removing the file
                    last_modified_image = max(self.images, key=lambda x: x.stat().st_mtime)
                    self.image_changed.emit(str(last_modified_image))

    def _get_image_files(self):
        image_files = []
        for file_path in Path(self.directory).iterdir():
            if file_path.is_file() and self._is_image_file(file_path.name):
                image_files.append(file_path)
        return image_files

    @staticmethod
    def _is_image_file(file_name):
        image_extensions = ['.tif', '.tiff']
        return any(file_name.lower().endswith(ext) for ext in image_extensions)

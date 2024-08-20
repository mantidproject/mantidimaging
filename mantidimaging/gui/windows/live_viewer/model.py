# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import time
from typing import TYPE_CHECKING
from pathlib import Path
from logging import getLogger

import dask.array
import numpy as np
from PyQt5.QtCore import QFileSystemWatcher, QObject, pyqtSignal, QTimer

import dask_image.imread
from astropy.io import fits

from mantidimaging.core.utility import ExecutionProfiler

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
    _selected_index: int

    def __init__(self, image_list: list[Image_Data], create_delayed_array: bool = True):
        self.image_list = image_list
        self.create_delayed_array = create_delayed_array

        if image_list and create_delayed_array:
            self.delayed_stack = self.create_delayed_stack_from_image_data(image_list)

    @property
    def shape(self):
        return self.delayed_stack.shape

    @property
    def selected_index(self):
        return self._selected_index

    @selected_index.setter
    def selected_index(self, index):
        self._selected_index = index

    def get_delayed_arrays(self, image_list: list[Image_Data]) -> list[dask.array.Array] | None:
        if image_list:
            if image_list[0].image_path.suffix.lower() in [".tif", ".tiff"] and self.create_delayed_array:
                return [dask_image.imread.imread(image_data.image_path)[0] for image_data in image_list]
            elif image_list[0].image_path.suffix.lower() == ".fits" and self.create_delayed_array:
                return [dask.delayed(fits.open)(image_data.image_path)[0].data for image_data in image_list]
            else:
                return None

    def get_delayed_image(self, index: int) -> dask.array.Array | None:
        return self.delayed_stack[index] if self.delayed_stack is not None else None

    def get_image_data(self, index: int) -> Image_Data | None:
        return self.image_list[index] if self.image_list else None

    def get_fits_sample(self, image_data: Image_Data) -> np.ndarray:
        with fits.open(image_data.image_path.__str__()) as fit:
            return fit[0].data

    def get_computed_image(self, index: int):
        if index < 0:
            return None
        try:
            self.get_delayed_image(index).compute()
            print(f"+++++++++++++++++++++++++++++++++++ get_computed_image {index=} ++++++++++++++++++++++++++++++")
            print(f"+++++++++++++++++++++++++++++++++++ get_computed_image {self.get_delayed_image(index)=} ++++++++++++++++++++++++++++++")
            print(
                f"+++++++++++++++++++++++++++++++++++ get_computed_image {self.get_image_data(index).image_path=} ++++++++++++++++++++++++++++++")
        except dask_image.imread.pims.api.UnknownFormatError:
            print(f"+++++++++++++++++++++++++++++++++++ get_computed_image FAILED {self.get_image_data(index).image_path=}++++++++++++++++++++++++++++++")
            self.remove_image_data_by_index(index)
            self.get_computed_image(index-1)
        except AttributeError:
            return None
        return self.get_delayed_image(index).compute()

    def get_selected_computed_image(self):
        try:
            self.get_computed_image(self.selected_index)
        except dask_image.imread.pims.api.UnknownFormatError:
            pass
        return self.get_computed_image(self.selected_index)

    def remove_image_data_by_path(self, image_path: Path) -> None:
        image_paths = [image.image_path for image in self.image_list]
        index_to_remove = image_paths.index(image_path)
        self.remove_image_data_by_index(index_to_remove)

    def remove_image_data_by_index(self, index_to_remove: int) -> None:
        self.image_list.pop(index_to_remove)
        print(f"KKKKKKKKKKKKK {self.delayed_stack=} KKKKKKKKKKKKKKKKKKKK")
        self.delayed_stack = dask.array.delete(self.delayed_stack, index_to_remove, 0)
        print(f"VVVVVVVVVVVVVVVVVVVVV {self.delayed_stack=} VVVVVVVVVVVVVVVVVVVVVV")
        if index_to_remove == self.selected_index and self.selected_index > 0:
            self.selected_index = self.selected_index - 1
        if not self.image_list:
            self.delayed_stack = None

    def create_delayed_stack_from_image_data(self, image_list: list[Image_Data]) -> None | dask.array.Array:
        delayed_stack = None
        arrays = self.get_delayed_arrays(image_list)
        if arrays:
            if image_list[0].image_path.suffix.lower() in [".tif", ".tiff"]:
                delayed_stack = dask.array.stack(dask.array.array(arrays))
            elif image_list[0].image_path.suffix.lower() in [".fits"]:
                sample = self.get_fits_sample(image_list[0])
                lazy_arrays = [dask.array.from_delayed(x, shape=sample.shape, dtype=sample.dtype) for x in arrays]
                delayed_stack = dask.array.stack(lazy_arrays)
            else:
                raise NotImplementedError(f"DaskImageDataStack does not support image with extension "
                                          f"{image_list[0].image_path.suffix.lower()}")
        return delayed_stack

    def add_images_to_delayed_stack(self, new_image_list: list[Image_Data]) -> None:
        if not new_image_list:
            return
        image_paths = [image.image_path for image in self.image_list]
        images_to_add = [image for image in new_image_list if image.image_path not in image_paths]
        print(f"============== {images_to_add=} ======================")
        if self.delayed_stack is None or dask.array.isnan(self.delayed_stack.shape).any():
            self.delayed_stack = self.create_delayed_stack_from_image_data(new_image_list)
        else:
            if images_to_add:
                self.delayed_stack = dask.array.concatenate([self.delayed_stack, self.get_delayed_arrays(images_to_add)])
        self.image_list.extend(images_to_add)
            # self.delayed_stack = dask.array.stack([self.delayed_stack, self.create_delayed_stack_from_image_data(image_list)])
            # self.delayed_stack = dask.array.unique(self.delayed_stack)

    def delete_all_data(self):
        self.image_list = []
        self.delayed_stack = None
        self.selected_index = 0


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
        self._images: list[Image_Data] = []
        self.image_stack: DaskImageDataStack = DaskImageDataStack([])

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

    def _handle_image_changed_in_list(self, image_files: list[Image_Data],
                                      dask_image_stack: DaskImageDataStack) -> None:
        """
        Handle an image changed event. Update the image in the view.
        This method is called when the image_watcher detects a change
        which could be a new image, edited image or deleted image.

        :param image_files: list of image files
        """
        print(f"++++++++++++++++ _handle_image_changed_in_list +++++++++++++++++++++")
        print(f"\n{[image.image_path for image in self.image_stack.image_list]=}\n")
        print(f"\n{[image.image_path for image in dask_image_stack.image_list]=}\n")
        print(f"\n{[image.image_path for image in image_files]=}\n")
        self.images = image_files
        self.image_stack = dask_image_stack
        # if dask_image_stack.image_list:
        #     self.image_stack = dask_image_stack
        self.presenter.update_image_list(image_files)
        self.presenter.update_image_stack(self.image_stack)

    def handle_image_modified(self, image_path: Path):
        print(f"++++++++++++++++ handle_image_modified +++++++++++++++++++++")
        print(f"\n{[image.image_path for image in self.image_stack.image_list]=}\n")
        print(f"\n{image_path=}\n")
        self.image_stack.remove_image_data_by_path(image_path)
        print(f"\n{[image.image_path for image in self.image_stack.image_list]=}\n")
        #print(f"\n{[self.image_stack.delayed_stack.shape]=}\n")
        self.presenter.update_image_modified(image_path)
        self.presenter.update_image_stack(self.image_stack)

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
    image_stack = DaskImageDataStack([], create_delayed_array=True)

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
        if len(images) == 0:
            self.image_stack.delete_all_data()
        self.image_stack.add_images_to_delayed_stack(images)
        print(f"\n ================== {len(self.image_stack.image_list)=} =========================\n")
        #print(f"\n ================== {self.image_stack.delayed_stack.shape=} =========================\n")
        if len(images) % 50 == 0:
            with ExecutionProfiler(msg=f"create delayed array and compute mean for {len(images)} images"):

                print(f"\n ================== {self.image_stack.delayed_stack=} =========================\n")
                print(f"\n ================== {self.image_stack.image_list=} =========================\n")
                print(f"\n ================== {len(self.image_stack.image_list)=} =========================\n")
                if self.image_stack.image_list:
                    arrmean = dask.array.mean(self.image_stack.delayed_stack, axis=(1, 2))
                    print(arrmean.compute())

        self.update_recent_watcher(images[-1:])
        self.image_changed.emit(images, self.image_stack)

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

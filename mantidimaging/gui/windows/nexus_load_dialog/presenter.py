# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import enum
import traceback
from enum import auto, Enum
from logging import getLogger
from typing import TYPE_CHECKING, Optional, Union

import h5py
import numpy as np

if TYPE_CHECKING:
    from mantidimaging.gui.windows.nexus_load_dialog.view import NexusLoadDialog  # pragma: no cover

logger = getLogger(__name__)


class Notification(Enum):
    NEXUS_FILE_SELECTED = auto()


class ImageKeys(enum.Enum):
    Projections = 0
    FlatField = 1
    DarkField = 2


IMAGE_TITLE_MAP = {ImageKeys.Projections: "Projections", ImageKeys.FlatField: "Flat", ImageKeys.DarkField: "Dark"}
BEFORE_TITLE_MAP = {True: "Before", False: "After"}

TOMO_ENTRY = "tomo_entry"
DATA_PATH = "instrument/detector/data"
IMAGE_KEY_PATH = "instrument/detector/image_key"


def _missing_data_message(field_name: str) -> str:
    """
    Creates a message for logging when a certain field is missing in the NeXus file.
    :param field_name: The name of the missing field.
    :return: A string telling the user that the field is missing.
    """
    return f"The NeXus file does not contain the required {field_name} field."


class NexusLoadPresenter:
    view: 'NexusLoadDialog'

    def __init__(self, view: 'NexusLoadDialog'):
        self.view = view
        self.nexus_file = None
        self.tomo_entry = None
        self.data = None
        self.tomo_path = ""
        self.image_key_dataset = None
        self.title = ""

    def notify(self, n: Notification):
        try:
            if n == Notification.NEXUS_FILE_SELECTED:
                self.scan_nexus_file()
        except RuntimeError as err:
            self.view.show_error(str(err), traceback.format_exc())

    def scan_nexus_file(self):
        file_path = self.view.filePathLineEdit.text()
        with h5py.File(file_path, "r") as self.nexus_file:
            self.tomo_entry = self._look_for_nxtomo_entry()
            if self.tomo_entry is None:
                error_msg = _missing_data_message(TOMO_ENTRY)
                logger.error(error_msg)
                self.view.invalid_file_opened()
                return

            self.image_key_dataset = self._look_for_tomo_data_and_update_view(IMAGE_KEY_PATH, 0)
            self.data = self._look_for_tomo_data_and_update_view(DATA_PATH, 1)
            self.title = self._find_data_title()

            if self.image_key_dataset is not None:
                self._get_data_from_image_key()

    def _missing_data_error(self, field: str):
        error_msg = _missing_data_message(field)
        logger.error(error_msg)
        self.view.show_error(error_msg)

    def _look_for_tomo_data_and_update_view(self, field: str, position: int):
        dataset = self._look_for_tomo_data(field)
        if dataset is None:
            self._missing_data_error(field)
            self.view.set_data_found(position, False, "", ())
        else:
            self.view.set_data_found(position, True, self.tomo_path + "/" + field, dataset.shape)
        return dataset

    def _look_for_nxtomo_entry(self) -> Optional[h5py.Group]:
        """
        Look for a tomo_entry field in the NeXus file.
        :return: The first tomo_entry group if one could be found, None otherwise.
        """
        for key in self.nexus_file.keys():
            if TOMO_ENTRY in self.nexus_file[key].keys():
                self.tomo_path = f"{key}/{TOMO_ENTRY}"
                return self.nexus_file[key][TOMO_ENTRY]
        return None

    def _look_for_tomo_data(self, entry_path: str) -> Optional[Union[h5py.Group, h5py.Dataset]]:
        """
        Retrieve data from the tomo entry field.
        :param entry_path: The path in which the data is found.
        :return: The Nexus group if it exists, None otherwise.
        """
        try:
            return self.tomo_entry[entry_path]
        except KeyError:
            return None

    def _get_data_from_image_key(self):
        """
        Looks for dark/flat before/after images to create a dataset.
        :return: The image Dataset and a list containing issue strings.
        """
        sample_array = self._get_images(ImageKeys.Projections)
        if sample_array.size == 0:
            self.view.set_images_found(0, False, sample_array.shape)
            self.view.invalid_file_opened()
            return
        else:
            self.view.set_images_found(0, True, sample_array.shape, False)

        dark_before_array = self._get_images(ImageKeys.DarkField, True)
        self.view.set_images_found(1, dark_before_array.size != 0, dark_before_array.shape)

        flat_before_array = self._get_images(ImageKeys.FlatField, True)
        self.view.set_images_found(2, flat_before_array.size != 0, flat_before_array.shape)

        flat_after_array = self._get_images(ImageKeys.FlatField, False)
        self.view.set_images_found(3, flat_after_array.size != 0, flat_before_array.shape)

        dark_after_array = self._get_images(ImageKeys.DarkField, False)
        self.view.set_images_found(4, dark_after_array.size != 0, dark_before_array.shape)

    def _get_images(self, image_key_number: ImageKeys, before: Optional[bool] = None) -> np.ndarray:
        """
        Retrieve images from the data based on an image key number.
        :param image_key_number: The image key number.
        :param before: True if the function should return before images, False if the function should return after
                       images. Ignored when getting projection images.
        :return: The set of images that correspond with a given image key.
        """
        if image_key_number is ImageKeys.Projections:
            indices = self.image_key_dataset[...] == image_key_number.value
        else:
            if before:
                indices = self.image_key_dataset[:self.image_key_dataset.size // 2] == image_key_number.value
            else:
                indices = self.image_key_dataset[:] == image_key_number.value
                indices[:self.image_key_dataset.size // 2] = False
        # Shouldn't have to use numpy.where but h5py doesn't allow indexing with bool arrays currently
        return self.data[np.where(indices)]

    def _generate_image_name(self, image_key_number: ImageKeys, before: Optional[bool] = None) -> str:
        """
        Creates a name for a group of images by using the image key.
        :param image_key_number: The image key number for the collection of images.
        :param before: True if before images, False if after images, None if the images are projections.
        :return: A string for the images name.
        """
        name = [IMAGE_TITLE_MAP[image_key_number]]
        if before is not None:
            name.append(BEFORE_TITLE_MAP[before])
        name.append(self.title)

        return " ".join(name)

    def _find_data_title(self) -> str:
        """
        Find the title field in the tomo_entry.
        :return: The title if it was found, "NeXus Data" otherwise.
        """
        try:
            return self.tomo_entry["title"][0].decode("UTF-8")
        except KeyError:
            return "NeXus Data"

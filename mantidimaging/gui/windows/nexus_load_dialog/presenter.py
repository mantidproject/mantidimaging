# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import enum
import traceback
from enum import auto, Enum
from logging import getLogger
from typing import TYPE_CHECKING, Optional, Union, Tuple

import h5py
import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset

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

        self.sample_array = None
        self.dark_before_array = None
        self.flat_before_array = None
        self.flat_after_array = None
        self.dark_after_array = None

    def notify(self, n: Notification):
        try:
            if n == Notification.NEXUS_FILE_SELECTED:
                self.scan_nexus_file()
        except RuntimeError as err:
            self.view.show_error(str(err), traceback.format_exc())

    def scan_nexus_file(self):
        """
        Try to open the NeXus file and display its contents on the view.
        """
        file_path = self.view.filePathLineEdit.text()
        with h5py.File(file_path, "r") as self.nexus_file:
            self.tomo_entry = self._look_for_nxtomo_entry()
            if self.tomo_entry is None:
                return

            self.image_key_dataset = self._look_for_tomo_data_and_update_view(IMAGE_KEY_PATH, 0)
            self.data = self._look_for_tomo_data_and_update_view(DATA_PATH, 1)
            if self.data is None:
                self.view.disable_ok_button()

            if self.image_key_dataset is not None:
                self._get_data_from_image_key()

            self.title = self._find_data_title()

    def _missing_data_error(self, field: str):
        """
        Create a missing data message and display it on the view.
        :param field: The name of the field that couldn't be found in the NeXus file.
        """
        error_msg = _missing_data_message(field)
        self.view.show_error(error_msg, "")

    def _look_for_tomo_data_and_update_view(self, field: str,
                                            position: int) -> Optional[Union[h5py.Group, h5py.Dataset]]:
        """
        Looks for the data in the NeXus file and adds information about it to the view if it's found.
        :param field: The name of the NeXus field.
        :param position: The position of the field information row in the view's QTreeWidget.
        :return: The h5py Group/Dataset if it could be found, None otherwise.
        """
        dataset = self._look_for_tomo_data(field)
        if dataset is None:
            self._missing_data_error(field)
            self.view.set_data_found(position, False, "", ())
        else:
            self.view.set_data_found(position, True, self.tomo_path + "/" + field, dataset.shape)
        return dataset

    def _look_for_nxtomo_entry(self) -> Optional[h5py.Group]:
        """
        Look for a tomo_entry field in the NeXus file. Generate an error and disable the view OK button if it can't be
        found.
        :return: The first tomo_entry group if one could be found, None otherwise.
        """
        for key in self.nexus_file.keys():
            if TOMO_ENTRY in self.nexus_file[key].keys():
                self.tomo_path = f"{key}/{TOMO_ENTRY}"
                return self.nexus_file[key][TOMO_ENTRY]

        self._missing_data_error(TOMO_ENTRY)
        self.view.disable_ok_button()
        return None

    def _look_for_tomo_data(self, entry_path: str) -> Optional[Union[h5py.Group, h5py.Dataset]]:
        """
        Retrieve data from the tomo entry field.
        :param entry_path: The path in which the data is found.
        :return: The Nexus Group/Dataset if it exists, None otherwise.
        """
        try:
            return self.tomo_entry[entry_path]
        except KeyError:
            return None

    def _get_data_from_image_key(self):
        """
        Looks for the projection and dark/flat before/after images and update the information on the view.
        """
        self.sample_array = self._get_images(ImageKeys.Projections)
        if self.sample_array.size == 0:
            self.view.set_images_found(0, False, self.sample_array.shape)
            self.view.disable_ok_button()
            return
        else:
            self.view.set_images_found(0, True, self.sample_array.shape, False)

        self.flat_before_array = self._get_images(ImageKeys.FlatField, True)
        self.view.set_images_found(1, self.flat_before_array.size != 0, self.flat_before_array.shape)

        self.flat_after_array = self._get_images(ImageKeys.FlatField, False)
        self.view.set_images_found(2, self.flat_after_array.size != 0, self.flat_before_array.shape)

        self.dark_before_array = self._get_images(ImageKeys.DarkField, True)
        self.view.set_images_found(3, self.dark_before_array.size != 0, self.dark_before_array.shape)

        self.dark_after_array = self._get_images(ImageKeys.DarkField, False)
        self.view.set_images_found(4, self.dark_after_array.size != 0, self.dark_before_array.shape)

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

    def _find_data_title(self) -> str:
        """
        Find the title field in the tomo_entry.
        :return: The title if it was found, "NeXus Data" otherwise.
        """
        try:
            return self.tomo_entry["title"][0].decode("UTF-8")
        except KeyError:
            return "NeXus Data"

    def get_dataset(self) -> Tuple[Dataset, str]:
        """
        Create a Dataset and title using the arrays that have been retrieved from the NeXus file.
        :return: A tuple containing the Dataset and the data title string.
        """
        return Dataset(sample=self._create_images(self.sample_array, "Projections"),
                       flat_before=self._create_images(self.flat_before_array, "Flat Before"),
                       flat_after=self._create_images(self.flat_after_array, "Flat After"),
                       dark_before=self._create_images(self.dark_before_array, "Dark Before"),
                       dark_after=self._create_images(self.dark_after_array, "Dark After")), self.title

    def _create_images(self, data_array: np.ndarray, name: str) -> Optional[Images]:
        """
        Create the Images objects using the data found in the NeXus file.
        :param data_array: The images data array.
        :param name: The name of the images.
        :return: An images object if the data could be found in the NeXus file and the "Use" checkbox is ticked in the
                 view, None otherwise.
        """
        if data_array.size == 0 or not self.view.checkboxes[name].isChecked():
            return None
        return Images(data_array, [f"{name} {self.title}"])

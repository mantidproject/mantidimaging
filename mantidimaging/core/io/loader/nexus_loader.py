# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import enum
from typing import Union, Optional, List, Tuple

import h5py
from logging import getLogger

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset

logger = getLogger(__name__)

TOMO_ENTRY_PATH = "/entry1/tomo_entry"
DATA_PATH = TOMO_ENTRY_PATH + "/data/data"
IMAGE_KEY_PATH = TOMO_ENTRY_PATH + "/instrument/detector/image_key"


class ImageKeys(enum.Enum):
    Projections = 0
    FlatField = 1
    DarkField = 2


def _missing_data_message(field_name: str) -> str:
    """
    Creates a message for logging when a certain field is missing in the NeXus file.
    :param field_name: The name of the missing field.
    :return: A string telling the user that the field is missing.
    """
    return f"The NeXus file does not contain the required {field_name} field."


def _missing_images_message(image_name: str) -> str:
    """
    Generate a message when certain images are missing from the NeXus file.
    :param image_name: The name of the missing images.
    :return: A string with a missing images message.
    """
    return f"No {image_name} images found in the NeXus file."


def _generate_image_name(image_key_number: ImageKeys, before: Optional[bool]) -> str:
    """
    Creates a name for a group of images by using the image key.
    :param image_key_number: The image key number for the collection of images.
    :param before: True if before images, False if after images.
    :return: A string for the images name.
    """
    if image_key_number == ImageKeys.Projections:
        return "Sample"
    elif image_key_number == ImageKeys.FlatField:
        name = "Flat"
    else:
        name = "Dark"

    if before:
        return name + " Before"
    return name + " After"


class NexusLoader:
    def __init__(self):
        """
        Load a Dataset from a NeXus file.
        """
        self.nexus_file = None
        self.tomo_entry = None
        self.data = None
        self.image_key_dataset = None
        self.issues = None

    def load_nexus_data(self, file_path: str) -> Tuple[Optional[Dataset], List[str]]:
        """
        Load the NeXus file and attempt to create a Dataset.
        :param file_path: The NeXus file path.
        :return: A Dataset containing sample, flat field, and dark field images if the file has the expected structure.
        """
        self.issues = []

        with h5py.File(file_path, 'r') as self.nexus_file:

            self.tomo_entry = self._get_tomo_data(TOMO_ENTRY_PATH)
            if self.tomo_entry is None:
                error_msg = _missing_data_message(TOMO_ENTRY_PATH)
                logger.error(error_msg)
                return None, [error_msg]

            self.data = self._get_tomo_data(DATA_PATH)
            if self.data is None:
                error_msg = _missing_data_message(DATA_PATH)
                logger.error(error_msg)
                return None, [error_msg]

            self.image_key_dataset = self._get_tomo_data(IMAGE_KEY_PATH)
            if self.image_key_dataset is None:
                return self._get_projections()
            else:
                return self._get_data_from_image_key()

    def _get_tomo_data(self, entry_path: str) -> Optional[Union[h5py.Group, h5py.Dataset]]:
        """
        Retrieve data from the NeXus file structure.
        :param entry_path: The path in which the data is found.
        :return: The Nexus group if it exists, None otherwise.
        """
        try:
            return self.nexus_file[entry_path]
        except KeyError:
            return None

    def _get_projections(self) -> Tuple[Dataset, List[str]]:
        """
        Treat all the images in the data array as projections, and return them in the form of a Dataset.
        :return: The image Dataset and a list containing an issue string.
        """
        no_img_key_msg = "No image key found. Treating all images as projections."
        logger.info(no_img_key_msg)
        return Dataset(Images(np.array(self.data))), [no_img_key_msg]

    def _get_data_from_image_key(self) -> Tuple[Optional[Dataset], List[str]]:
        """
        Looks for dark/flat before/after images to create a dataset.
        :return: The image Dataset and a list containing issue strings.
        """
        sample_array = self._get_images(ImageKeys.Projections)
        if sample_array.size == 0:
            error_msg = _missing_images_message("projection")
            logger.error(error_msg)
            return None, [error_msg]

        dark_before_images = self._find_before_after_images(ImageKeys.DarkField, True)
        flat_before_images = self._find_before_after_images(ImageKeys.FlatField, True)
        flat_after_images = self._find_before_after_images(ImageKeys.FlatField, False)
        dark_after_images = self._find_before_after_images(ImageKeys.DarkField, False)

        return Dataset(Images(sample_array, [DATA_PATH]),
                       flat_before=flat_before_images,
                       flat_after=flat_after_images,
                       dark_before=dark_before_images,
                       dark_after=dark_after_images), self.issues

    def _get_images(self, image_key_number: ImageKeys, before: Optional[bool] = None) -> np.array:
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

    def _find_before_after_images(self, image_key_number: ImageKeys, before: bool) -> Optional[Images]:
        """
        Looks for dark/flat before/after images in the data field using the image key.
        :param image_key_number: The image key number of the images.
        :param before: True for before images, False for after images.
        :return: The images if they were found, None otherwise.
        """
        image_name = _generate_image_name(image_key_number, before)
        images_array = self._get_images(image_key_number, before)
        if images_array.size == 0:
            info_msg = _missing_images_message(image_name)
            logger.info(info_msg)
            self.issues.append(info_msg)
            return None
        else:
            return Images(images_array, [image_name])

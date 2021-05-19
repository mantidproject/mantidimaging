# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import enum
from typing import Union, Optional

import h5py
from logging import getLogger

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset

logger = getLogger(__name__)

TOMO_ENTRY_PATH = "/entry1/tomo_entry"
DATA_PATH = TOMO_ENTRY_PATH + "/data"
IMAGE_KEY_PATH = TOMO_ENTRY_PATH + "/image_key"


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


def _get_tomo_data(nexus_data: Union[h5py.File, h5py.Group],
                   entry_path: str) -> Optional[Union[h5py.Group, h5py.Dataset]]:
    """
    Retrieve data from the NeXus file structure.
    :param nexus_data: The NeXus file or group.
    :param entry_path: The path in which the data is found.
    :return: The Nexus group if it exists, None otherwise.
    """
    try:
        return nexus_data[entry_path]
    except KeyError:
        logger.error(_missing_data_message(entry_path))
        return None


def _load_nexus_file(file_path: str) -> h5py.File:
    """
    Load a NeXus file.
    :param file_path: The NeXus file path.
    :return: The h5py File object.
    """
    return h5py.File(file_path, 'r')


def _get_images(image_key_number: ImageKeys,
                image_key: h5py.Dataset,
                data: h5py.Dataset,
                before: Optional[bool] = None) -> np.array:
    """
    Retrieve images from the data based on an image key number.
    :param image_key_number: The image key number.
    :param image_key: The image key array.
    :param data: The entire data array.
    :param before: True if the function should return before images, False if the function should return after images.
                   Ignored when getting projection images.
    :return: The set of images that correspond with a given image key.
    """
    if image_key_number is ImageKeys.Projections:
        indices = image_key[...] == image_key_number.value
    else:
        if before:
            indices = image_key[:image_key.size // 2] == image_key_number.value
        else:
            indices = image_key[:] == image_key_number.value
            indices[:image_key.size // 2] = False
    # Shouldn't have to use numpy.where but h5py doesn't allow indexing with bool arrays currently
    return data[np.where(indices)]


def load_nexus_data(file_path: str) -> Optional[Dataset]:
    """
    Load the NeXus file and attempt to create a Dataset.
    :param file_path: The NeXus file path.
    :return: A Dataset containing sample, flat field, and dark field images if the file has the expected structure.
    """
    nexus_file = _load_nexus_file(file_path)

    tomo_entry = _get_tomo_data(nexus_file, TOMO_ENTRY_PATH)
    if tomo_entry is None:
        return None

    data = _get_tomo_data(nexus_file, DATA_PATH)
    image_key = _get_tomo_data(nexus_file, IMAGE_KEY_PATH)

    if data is None or image_key is None:
        return None

    sample_array = _get_images(ImageKeys.Projections, image_key, data)
    if sample_array.size == 0:
        logger.error(_missing_images_message("sample"))
        return None

    flat_before_array = _get_images(ImageKeys.FlatField, image_key, data, True)
    if flat_before_array.size == 0:
        logger.info(_missing_images_message("flat before"))
        flat_before_images = None
    else:
        flat_before_images = Images(flat_before_array, ["flat before"])

    flat_after_array = _get_images(ImageKeys.FlatField, image_key, data, False)
    if flat_after_array.size == 0:
        logger.info(_missing_images_message("flat after"))
        flat_after_images = None
    else:
        flat_after_images = Images(flat_after_array, ["flat after"])

    dark_before_array = _get_images(ImageKeys.DarkField, image_key, data, True)
    if dark_before_array.size == 0:
        logger.info(_missing_images_message("dark before"))
        dark_before_images = None
    else:
        dark_before_images = Images(dark_before_array, ["dark before"])

    dark_after_array = _get_images(ImageKeys.DarkField, image_key, data, False)
    if dark_after_array.size == 0:
        logger.info(_missing_images_message("dark after"))
        dark_after_images = None
    else:
        dark_after_images = Images(dark_after_array, ["dark after"])

    nexus_file.close()

    return Dataset(Images(sample_array, [DATA_PATH]),
                   flat_before=flat_before_images,
                   flat_after=flat_after_images,
                   dark_before=dark_before_images,
                   dark_after=dark_after_images)

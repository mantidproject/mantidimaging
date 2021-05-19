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


def get_tomo_data(nexus_data: Union[h5py.File, h5py.Group],
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
    with h5py.File(file_path, 'r') as nexus_file:
        return nexus_file


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
    :return: The set of images that correspond with a given image key.
    """
    if image_key_number is ImageKeys.Projections:
        indices = image_key[...] == image_key_number.value
    else:
        image_key_copy = image_key[:]
        if before:
            image_key_copy[:image_key.size // 2] = 0
        else:
            image_key_copy[image_key.size // 2:] = 0
        indices = image_key_copy[...] == image_key_number.value
    return data[np.where(indices)]  # Current h5py issue


def load_nexus_data(file_path: str) -> Optional[Dataset]:
    """
    Load the NeXus file and attempt to create a Dataset.
    :param file_path: The NeXus file path.
    :return: A Dataset containing sample, flat field, and dark field images if the file has the expected structure.
    """
    missing_data = False
    nexus_file = _load_nexus_file(file_path)

    tomo_entry = get_tomo_data(nexus_file, TOMO_ENTRY_PATH)
    if tomo_entry is None:
        return None

    data = get_tomo_data(nexus_file, DATA_PATH)
    if data is None:
        missing_data = True

    image_key = get_tomo_data(nexus_file, IMAGE_KEY_PATH)
    if image_key is None:
        missing_data = True

    if missing_data:
        return None

    sample = _get_images(ImageKeys.Projections, image_key, data)
    if sample.size == 0:
        logger.error("No sample images found in NeXus file.")
        return None

    flat_before_array = _get_images(ImageKeys.FlatField, image_key, data, True)
    if flat_before_array.size == 0:
        logger.info("No flat before images found in the NeXus file.")
        flat_before_images = None
    else:
        flat_before_images = Images(flat_before_array)

    flat_after_array = _get_images(ImageKeys.FlatField, image_key, data, False)
    if flat_after_array.size == 0:
        logger.info("No flat after images found in the NeXus file.")
        flat_after_images = None
    else:
        flat_after_images = Images(flat_after_array)

    dark_before_array = _get_images(ImageKeys.DarkField, image_key, data, True)
    if dark_before_array.size == 0:
        logger.info("No dark before images found in the NeXus file.")
        dark_before_images = None
    else:
        dark_before_images = Images(dark_before_array)

    dark_after_array = _get_images(ImageKeys.DarkField, image_key, data, False)
    if dark_after_array.size == 0:
        logger.info("No dark after images found in the NeXus file.")
        dark_after_images = None
    else:
        dark_after_images = Images(dark_after_array)

    return Dataset(Images(sample),
                   flat_before=flat_before_images,
                   flat_after=flat_after_images,
                   dark_before=dark_before_images,
                   dark_after=dark_after_images)

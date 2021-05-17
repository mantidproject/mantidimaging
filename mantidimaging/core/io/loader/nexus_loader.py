from typing import Union, Optional

import h5py
from logging import getLogger

logger = getLogger(__name__)


def _missing_field_message(field_name: str) -> str:
    """
    Creates a message for logging when a certain field is missing in the NeXus file.
    :param field_name: The name of the missing field.
    :return: A string telling the user that the field is missing.
    """
    return f"The NeXus file does not contain the required {field_name} field."


def get_tomo_data(nexus_data: Union[h5py.File, h5py.Group], entry_path: str) -> Optional[h5py.Group]:
    """
    Retrieve data from the NeXus file structure.
    :param nexus_data: The NeXus file or group.
    :param entry_path: The path in which the data is found.
    :return: The Nexus group if it exists, None otherwise.
    """
    try:
        return nexus_data[entry_path]
    except KeyError:
        return None


def load_nexus_data(file_path: str):
    with h5py.File(file_path, 'r') as nexus_file:
        tomo_entry = get_tomo_data(nexus_file, '/entry1/tomo_entry')
        if tomo_entry is None:
            logger.error(_missing_field_message('tomo_entry'))
            return
        data = get_tomo_data(tomo_entry, 'data')
        if data is None:
            logger.error(_missing_field_message('tomo_entry/data'))
            return
        image_key = get_tomo_data(tomo_entry, 'image_key')
        if image_key is None:
            logger.error(_missing_field_message('tomo_entry/image_key'))
            return

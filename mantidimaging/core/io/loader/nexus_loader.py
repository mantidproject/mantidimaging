from typing import Union, Optional

import h5py
from logging import getLogger

logger = getLogger(__name__)

def get_tomo_data(nexus_data: Union[h5py._hl.files.File, h5py._hl.group.Group], entry_path: str) -> Optional[h5py._hl.group.Group]:
    """
    Retrieve data from the NeXus file structure.
    :param nexus_data: The NeXus file or group.
    :param entry_path: The path in which the data is found.
    :return:
    """
    try:
        return nexus_data[entry_path]
    except KeyError:
        return None


def execute(file_path: str):
    with h5py.File(file_path, 'r') as nexus_file:
        tomo_entry = get_tomo_data(nexus_file, '/entry1/tomo_entry')
        if tomo_entry is None:
            logger.error("NeXus file does not contain ")
            return
        data = get_tomo_data(tomo_entry, 'data')
        if data is None:
            return
        image_key = get_tomo_data(tomo_entry, 'image_key')
        if image_key is None:
            return

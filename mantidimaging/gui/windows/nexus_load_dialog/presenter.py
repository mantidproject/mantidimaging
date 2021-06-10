# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import traceback
from enum import auto, Enum
from logging import getLogger
from typing import TYPE_CHECKING, Optional, Union

import h5py

if TYPE_CHECKING:
    from mantidimaging.gui.windows.nexus_load_dialog.view import NexusLoadDialog  # pragma: no cover

logger = getLogger(__name__)


class Notification(Enum):
    NEXUS_FILE_SELECTED = auto()


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

    def notify(self, n: Notification, **baggage):
        try:
            if n == Notification.NEXUS_FILE_SELECTED:
                if not baggage:
                    return
                self.scan_nexus_file(**baggage)
        except RuntimeError as err:
            self.view.show_error(str(err), traceback.format_exc())

    def scan_nexus_file(self, file_path: str):
        with h5py.File(file_path, "r") as self.nexus_file:
            self.tomo_entry = self._find_tomo_entry()
            if self.tomo_entry is None:
                error_msg = _missing_data_message(TOMO_ENTRY)
                logger.error(error_msg)
                self.view.show_error(error_msg)
                return

            self.data = self._get_tomo_data(DATA_PATH)
            if self.data is None:
                error_msg = _missing_data_message(DATA_PATH)
                logger.error(error_msg)
                self.view.show_error(error_msg)
                return

            self.view.set_data_found(1, True, self.tomo_path + DATA_PATH)
            #
            # self.title = self._find_data_title()
            #
            # self.image_key_dataset = self._get_tomo_data(IMAGE_KEY_PATH)
            # if self.image_key_dataset is None:
            #     return self._get_projections()
            # else:
            #     return self._get_data_from_image_key()

    def _find_tomo_entry(self) -> Optional[h5py.Group]:
        """
        Look for a tomo_entry field in the NeXus file.
        :return: The first tomo_entry group if one could be found, None otherwise.
        """
        for key in self.nexus_file.keys():
            if TOMO_ENTRY in self.nexus_file[key].keys():
                self.tomo_path = f"{key}/{TOMO_ENTRY}"
                return self.nexus_file[key][TOMO_ENTRY]
        return None

    def _get_tomo_data(self, entry_path: str) -> Optional[Union[h5py.Group, h5py.Dataset]]:
        """
        Retrieve data from the tomo entry field.
        :param entry_path: The path in which the data is found.
        :return: The Nexus group if it exists, None otherwise.
        """
        try:
            return self.tomo_entry[entry_path]
        except KeyError:
            return None

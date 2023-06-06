# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import enum
import traceback
from enum import auto, Enum
from logging import getLogger
from typing import TYPE_CHECKING, Optional, Union, Tuple, List

import h5py
import numpy as np
from mantidimaging.core.data.reconlist import ReconList

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.core.io.utility import NEXUS_PROCESSED_DATA_PATH
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.data_containers import ProjectionAngles

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
ROTATION_ANGLE_PATH = "sample/rotation_angle"
DEFINITION = "definition"
NXTOMOPROC = "NXtomoproc"


def _missing_data_message(data_string: str) -> str:
    """
    Creates a message for logging when certain data is missing in the NeXus file.
    :param data_string: The name of the missing data.
    :return: A string telling the user that the data is missing.
    """
    return f"The NeXus file does not contain the {data_string} data."


class NexusLoadPresenter:
    view: 'NexusLoadDialog'

    def __init__(self, view: 'NexusLoadDialog'):
        self.view = view
        self.nexus_file = None
        self.tomo_entry = None
        self.data = None
        self.tomo_path = ""
        self.image_key_dataset = None
        self.rotation_angles = None
        self.title = ""
        self.recon_data: List[np.array] = []

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
            self.view.show_exception(str(err), traceback.format_exc())

    def scan_nexus_file(self):
        """
        Try to open the NeXus file and display its contents on the view.
        """
        file_path = self.view.filePathLineEdit.text()
        try:
            with h5py.File(file_path, "r") as self.nexus_file:
                self.tomo_entry = self._look_for_nxtomo_entry()
                if self.tomo_entry is None:
                    return

                self.data = self._look_for_image_data_and_update_view()
                if self.data is None:
                    return

                self.image_key_dataset = self._look_for_tomo_data_and_update_view(IMAGE_KEY_PATH, 0)
                if self.image_key_dataset is None:
                    return

                self.image_key_dataset = self.image_key_dataset[:]

                self.rotation_angles = self._look_for_tomo_data_and_update_view(ROTATION_ANGLE_PATH, 1)
                if self.rotation_angles is None:
                    return

                if "units" not in self.rotation_angles.attrs.keys():
                    logger.warning("No unit information found for rotation angles. Will infer from array values.")
                    degrees = np.abs(self.rotation_angles).max() > 2 * np.pi
                else:
                    degrees = "deg" in self.rotation_angles.attrs["units"]
                if degrees:
                    self.rotation_angles = np.radians(self.rotation_angles)
                self.rotation_angles = self.rotation_angles[:]

                self._look_for_recon_entries()

                self._get_data_from_image_key()
                self.title = self._find_data_title()
        except OSError:
            unable_message = f"Unable to read NeXus data from {file_path}"
            logger.error(unable_message)
            self.view.show_data_error(unable_message)
            self.view.disable_ok_button()

    def _read_rotation_angles(self, image_key: int, before: bool | None = None) -> Optional[np.ndarray]:
        """
        Reads the rotation angles array and coverts them to radians if needed.
        :param image_key: The image key for the angles to read.
        :param before: Whether the rotation angles are for before/after images. This is None when rotation angles
            for sample images are being read.
        :return: A numpy array of the rotation angles or None if all angles provided are 0.
        """
        assert self.image_key_dataset is not None
        if before is None:
            rotation_angles = self.rotation_angles[np.where(self.image_key_dataset[...] == image_key)]
        else:
            first_sample_image_index = np.where(self.image_key_dataset == 0)[0][0]
            if before:
                rotation_angles = self.rotation_angles[:first_sample_image_index][np.where(
                    self.image_key_dataset[:first_sample_image_index] == image_key)]
            else:
                rotation_angles = self.rotation_angles[first_sample_image_index:][np.where(
                    self.image_key_dataset[first_sample_image_index:] == image_key)]

        return rotation_angles if np.any(rotation_angles) else None

    def _missing_data_error(self, field: str):
        """
        Create a missing data message and display it on the view.
        :param field: The name of the field that couldn't be found in the NeXus file.
        """
        if "rotation_angle" in field:
            error_msg = _missing_data_message(field)
            logger.warning(error_msg)
        else:
            error_msg = _missing_data_message("required " + field)
            logger.error(error_msg)

        self.view.show_data_error(error_msg)

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
            self.view.disable_ok_button()
        else:
            self.view.set_data_found(position, True, self.tomo_path + "/" + field, dataset.shape)
        return dataset

    def _look_for_image_data_and_update_view(self) -> Optional[h5py.Dataset]:
        position = 2
        dataset = self._look_for_tomo_data(DATA_PATH)
        if dataset is not None:
            self.view.set_data_found(position, True, self.tomo_path + "/" + DATA_PATH, dataset.shape)
            return dataset
        else:
            assert self.nexus_file is not None
            if NEXUS_PROCESSED_DATA_PATH in self.nexus_file:
                dataset = self.nexus_file[NEXUS_PROCESSED_DATA_PATH]["data"]
                self.view.set_data_found(position, True, NEXUS_PROCESSED_DATA_PATH, dataset.shape)
                return dataset

        self._missing_data_error(DATA_PATH)
        self.view.set_data_found(position, False, "", ())
        self.view.disable_ok_button()
        return None

    def _look_for_nxtomo_entry(self) -> Optional[h5py.Group]:
        """
        Look for a tomo_entry field in the NeXus file. Generate an error and disable the view OK button if it can't be
        found.
        :return: The first tomo_entry group if one could be found, None otherwise.
        """
        assert self.nexus_file is not None
        for key in self.nexus_file.keys():
            if TOMO_ENTRY in self.nexus_file[key].keys():
                self.tomo_path = f"{key}/{TOMO_ENTRY}"
                return self.nexus_file[key][TOMO_ENTRY]

        self._missing_data_error(TOMO_ENTRY)
        self.view.disable_ok_button()
        return None

    def _look_for_recon_entries(self):
        """
        Tries to find recon entries in the NeXus file then stores the data in a list.
        """
        assert self.nexus_file is not None
        for key in self.nexus_file.keys():
            if DEFINITION in self.nexus_file[key].keys():
                if np.array(self.nexus_file[key][DEFINITION]).tobytes().decode("utf-8") == NXTOMOPROC:
                    nexus_recon = self.nexus_file[key]
                    self.recon_data.append(np.array(nexus_recon["data"]["data"]))

    def _look_for_tomo_data(self, entry_path: str) -> Optional[Union[h5py.Group, h5py.Dataset]]:
        """
        Retrieve data from the tomo entry field.
        :param entry_path: The path in which the data is found.
        :return: The Nexus Group/Dataset if it exists, None otherwise.
        """
        assert self.tomo_entry is not None
        try:
            return self.tomo_entry[entry_path]
        except KeyError:
            return None

    def _get_data_from_image_key(self):
        """
        Looks for the projection and dark/flat before/after images and update the information on the view.
        """
        self.sample_array = self._get_images(ImageKeys.Projections)
        self.view.set_images_found(0, self.sample_array.size != 0, self.sample_array.shape)
        if self.sample_array.size == 0:
            self._missing_data_error("projection images")
            self.view.disable_ok_button()
            return
        self.view.set_projections_increment(self.sample_array.shape[0])

        self.flat_before_array = self._get_images(ImageKeys.FlatField, True)
        self.view.set_images_found(1, self.flat_before_array.size != 0, self.flat_before_array.shape)

        self.flat_after_array = self._get_images(ImageKeys.FlatField, False)
        self.view.set_images_found(2, self.flat_after_array.size != 0, self.flat_after_array.shape)

        self.dark_before_array = self._get_images(ImageKeys.DarkField, True)
        self.view.set_images_found(3, self.dark_before_array.size != 0, self.dark_before_array.shape)

        self.dark_after_array = self._get_images(ImageKeys.DarkField, False)
        self.view.set_images_found(4, self.dark_after_array.size != 0, self.dark_after_array.shape)

    def _get_images(self, image_key_number: ImageKeys, before: Optional[bool] = None) -> np.ndarray:
        """
        Retrieve images from the data based on an image key number.
        :param image_key_number: The image key number.
        :param before: True if the function should return before images, False if the function should return after
                       images. Ignored when getting projection images.
        :return: The set of images that correspond with a given image key.
        """
        assert self.image_key_dataset is not None
        assert self.data is not None
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
        assert self.tomo_entry is not None
        try:
            return self.tomo_entry["title"][0].decode("UTF-8")
        except (KeyError, ValueError):
            logger.info("A valid title couldn't be found. Using 'NeXus Data' instead.")
            return "NeXus Data"

    def get_dataset(self) -> Tuple[StrictDataset, str]:
        """
        Create a LoadingDataset and title using the arrays that have been retrieved from the NeXus file.
        :return: A tuple containing the Dataset and the data title string.
        """
        sample_images = self._create_sample_images()
        sample_images.name = self.title
        ds = StrictDataset(sample=sample_images,
                           flat_before=self._create_images_if_required(self.flat_before_array, "Flat Before",
                                                                       ImageKeys.FlatField.value),
                           flat_after=self._create_images_if_required(self.flat_after_array, "Flat After",
                                                                      ImageKeys.FlatField.value),
                           dark_before=self._create_images_if_required(self.dark_before_array, "Dark Before",
                                                                       ImageKeys.DarkField.value),
                           dark_after=self._create_images_if_required(self.dark_after_array, "Dark After",
                                                                      ImageKeys.DarkField.value),
                           name=self.title)

        if self.recon_data:
            recon_list = self._create_recon_list()
            ds.recons = recon_list

        return ds, self.title

    def _create_sample_images(self):
        """
        Creates the sample ImageStack object.
        :return: An ImageStack object containing projections. If given, projection angles, pixel size, and 180deg are
            also set.
        """
        assert self.sample_array is not None

        # Create sample array and ImageStack object
        self.sample_array = self.sample_array[self.view.start_widget.value():self.view.stop_widget.value():self.view.
                                              step_widget.value()]
        sample_images = self._create_images(self.sample_array, "Projections")

        # Set attributes
        sample_images.pixel_size = int(self.view.pixelSizeSpinBox.value())
        projection_angles = self._read_rotation_angles(ImageKeys.Projections.value)
        if projection_angles is not None:
            sample_images.set_projection_angles(
                ProjectionAngles(projection_angles[self.view.start_widget.value():self.view.stop_widget.value():self.
                                                   view.step_widget.value()]))
        return sample_images

    def _create_images(self, data_array: np.ndarray, name: str) -> ImageStack:
        """
        Use a data array to create an ImageStack object.
        :param data_array: The images array obtained from the NeXus file.
        :param name: The name of the image dataset.
        :return: An ImageStack object.
        """
        data = pu.create_array(data_array.shape, self.view.pixelDepthComboBox.currentText())
        data.array[:] = data_array
        return ImageStack(data, [f"{name} {self.title}"])

    def _create_images_if_required(self, data_array: np.ndarray, name: str, image_key: int) -> Optional[ImageStack]:
        """
        Create the ImageStack objects if the corresponding data was found in the NeXus file, and the user checked the
        "Use?" checkbox.
        :param data_array: The images data array.
        :param name: The name of the images.
        :param image_key: The image key index for the image type.
        :return: An ImageStack object or None.
        """
        if data_array.size == 0 or not self.view.checkboxes[name].isChecked():
            return None
        image_stack = self._create_images(data_array, name)
        if image_stack is not None:
            projection_angles = self._read_rotation_angles(image_key, "Before" in name)
            if projection_angles is not None:
                image_stack.set_projection_angles(ProjectionAngles(projection_angles))
        return image_stack

    def _create_recon_list(self) -> ReconList:
        """
        Uses the array of recon data extracted from the NeXus file to create a ReconList object.
        :return: The ReconList object containing recons from the NeXus file.
        """
        recon_list = ReconList()
        for recon_array in self.recon_data:
            recon_list.append(ImageStack(recon_array))
        return recon_list

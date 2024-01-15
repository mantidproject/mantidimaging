# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import csv
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import numpy as np

from logging import getLogger
from mantidimaging.core.data import ImageStack
from mantidimaging.core.io.csv_output import CSVOutput
from mantidimaging.core.io import saver
from mantidimaging.core.io.instrument_log import LogColumn
from mantidimaging.core.utility.sensible_roi import SensibleROI

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.presenter import SpectrumViewerWindowPresenter

LOG = getLogger(__name__)

ROI_ALL = "all"
ROI_RITS = "rits_roi"


class SpecType(Enum):
    SAMPLE = 1
    OPEN = 2
    SAMPLE_NORMED = 3


class SpectrumViewerWindowModel:
    """
    The model for the spectrum viewer window.
    This model is responsible for storing the state of the window and providing
    the presenter with the data it needs to update the view.
    The model is also responsible for saving ROI data to a csv file.
    """
    presenter: 'SpectrumViewerWindowPresenter'
    _stack: Optional[ImageStack] = None
    _normalise_stack: Optional[ImageStack] = None
    tof_range: tuple[int, int] = (0, 0)
    _roi_ranges: dict[str, SensibleROI]

    def __init__(self, presenter: 'SpectrumViewerWindowPresenter'):
        self.presenter = presenter
        self._roi_id_counter = 0
        self._roi_ranges = {}
        self.special_roi_list = [ROI_ALL]
        self.bin_size: int = 10
        self.step_size: int = 1

    def roi_name_generator(self) -> str:
        """
        Returns a new Unique ID for newly created ROIs

        :return: A new unique ID
        """
        new_name = f"roi_{self._roi_id_counter}" if self._roi_id_counter > 0 else "roi"
        self._roi_id_counter += 1
        return new_name

    def get_list_of_roi_names(self) -> list[str]:
        """
        Get a list of rois available in the model
        """
        return list(self._roi_ranges.keys())

    def set_stack(self, stack: Optional[ImageStack]) -> None:
        """
        Sets the stack to be used by the model
        If that stack is None, then the model will be reset
        If the stack has changed, then the ROI ranges will be reset
        and additional ROIs excluding default ROIs will be removed

        @param stack: The new stack to be used by the model
        """

        self._stack = stack
        if stack is None:
            return
        self._roi_id_counter = 0
        self.tof_range = (0, stack.data.shape[0] - 1)
        self.set_new_roi(ROI_ALL)

    def set_new_roi(self, name: str) -> None:
        """
        Sets a new ROI with the given name

        @param name: The name of the new ROI
        """
        height, width = self.get_image_shape()
        self.set_roi(name, SensibleROI.from_list([0, 0, width, height]))

    def set_normalise_stack(self, normalise_stack: Optional[ImageStack]) -> None:
        self._normalise_stack = normalise_stack

    def set_roi(self, roi_name: str, roi: SensibleROI):
        self._roi_ranges[roi_name] = roi

    def get_roi(self, roi_name: str) -> SensibleROI:
        """
        Get the ROI with the given name from the model

        @param roi_name: The name of the ROI to get
        @return: The ROI with the given name
        """
        if roi_name not in self._roi_ranges.keys():
            raise KeyError(f"ROI {roi_name} does not exist in roi_ranges {self._roi_ranges.keys()}")
        return self._roi_ranges[roi_name]

    def get_averaged_image(self) -> Optional['np.ndarray']:
        """
        Get the averaged image from the stack in the model returning as a numpy array
        or None if it does not
        """
        if self._stack is not None:
            tof_slice = slice(self.tof_range[0], self.tof_range[1] + 1)
            return self._stack.data[tof_slice].mean(axis=0)
        return None

    @staticmethod  # option imagestack or sensible roi
    def get_stack_spectrum(stack, roi) -> 'np.ndarray':
        left, top, right, bottom = roi
        roi_data = stack.data[:, top:bottom, left:right]
        return roi_data.mean(axis=(1, 2))

    def normalise_issue(self) -> str:
        if self._stack is None or self._normalise_stack is None:
            return "Need 2 selected stacks"
        if self._stack is self._normalise_stack:
            return "Need 2 different stacks"
        if self._stack.data.shape != self._normalise_stack.data.shape:
            return "Stack shapes must match"
        return ""

    def set_bin_and_step_size(self, bin_size: int, step_size: int) -> None:
        """
        Set the bin size and step size for the region of interest (ROI).

        The bin size and step size are used when computing spectra for a sub-region of the ROI.
        The bin size determines the size of the sub-region, and the step size determines the number
        of pixels the sub-region moves in each step.

        If these paramreters are set to any value larger than zero, the method will compute a binned spectrum on export.

        Parameters:
        bin_size (int): The size of the sides of the sub-region of the ROI. Determines the size of the sub-region.
        step_size (int): The number of pixels the sub-region moves in each step.

        Returns:
        None
        """
        self.bin_size = bin_size
        self.step_size = step_size

    def normalise_spectrum(self, roi: SensibleROI) -> 'np.ndarray':
        """
        Normalise the spectrum for a given region of interest (ROI) by dividing it by the normalisation spectrum for
        the same ROI. The method first retrieves the spectrum for the given ROI from the stack and the normalisation
        spectrum from the normalisation stack.

        It then divides the ROI spectrum by the normalisation spectrum, element-wise.
        If an element in the normalisation spectrum is zero, the corresponding element in the output will be
        zero to avoid division by zero.

        Parameters:
        roi (SensibleROI): The region of interest for which the spectrum is to be normalised.

        Returns:
        np.ndarray: The normalised spectrum for the given ROI. The shape of the returned array matches
        the input spectrum.
        """
        roi_spectrum = self.get_stack_spectrum(self._stack, roi)
        roi_norm_spectrum = self.get_stack_spectrum(self._normalise_stack, roi)
        return np.divide(roi_spectrum, roi_norm_spectrum, out=np.zeros_like(roi_spectrum), where=roi_norm_spectrum != 0)

    def compute_spectra_for_rolling_sub_roi(self,
                                            roi: SensibleROI,
                                            sub_roi: SensibleROI,
                                            step: int = 1) -> 'np.ndarray':
        """
        Compute and return a list of spectra for a sub-region of interest (sub_roi) as it moves across a larger region
        of interest (roi).

        The sub_roi moves across the roi in steps specified by the 'step' parameter. It moves horizontally until it
        reaches the right edge of the roi,then it moves down by the step size in pixels and repeats the process until
        it reaches the bottom of the roi.

        If the step size is equal to the size of the sub_roi, then the sub_roi will perform a tile scan.
        Please note that if the step size is equal too or larger than the size of the roi on a given axis,
        then no spectra may be computed.

        For each position of the sub_roi, a spectrum is computed and added to a list.
        The spectrum is normalised using the 'normalise_spectrum' method.

        Parameters:
        roi (SensibleROI): The larger region of interest.
        sub_roi (SensibleROI): The sub-region of interest that moves across the roi.
        step (int, optional): The number of pixels the sub_roi moves in each step. Defaults to 1.

        Returns:
        list: A list of normalised spectra computed for each position of the sub_roi within the roi.
        """
        spectrum_list = []
        left, _, right, bottom = roi
        sub_left, sub_top, sub_right, sub_bottom = sub_roi

        while sub_right < right or sub_bottom < bottom:
            sub_roi = SensibleROI.from_list([sub_left, sub_top, sub_right, sub_bottom])
            spectrum_list.append(self.normalise_spectrum(sub_roi))
            if sub_right < right:
                sub_left, sub_right = sub_left + step, sub_right + step
            else:
                sub_left, sub_right = left, left + sub_roi.width
                sub_bottom, sub_top = sub_bottom + step, sub_top + step
        sub_roi = SensibleROI.from_list([sub_left, sub_top, sub_right, sub_bottom])
        spectrum_list.append(self.normalise_spectrum(sub_roi))
        return spectrum_list

    def compute_spectra_for_sub_roi(self, roi: SensibleROI, voxel_size: int, step_size: int = 1) -> 'np.ndarray':
        """
        Compute spectra for a sub-region of interest (sub_roi) within a larger region of interest (roi).

        The sub_roi is defined as a square with its top left corner at the top left corner of the roi and
        with sides of length equal to the voxel_size. The sub_roi "rolls" or moves across the roi, and for each
        position, a spectrum is computed and added to a list. The movement of the sub_roi across the roi is
        controlled by the step_size parameter.
        If the step size is equal to the voxel_size, then the sub_roi will perform a tile scan.

        Parameters:
        roi (SensibleROI): The larger region of interest.
        voxel_size (int): The size of the sides of the sub_roi. Determines the size of the sub_roi.
        step_size (int, optional): The number of pixels the sub_roi moves in each step. Defaults to 1.

        Returns:
        np.ndarray: An array of spectra computed for each position of the sub_roi within the roi.
        """
        left, top, _, _ = roi
        new_right = left + voxel_size
        new_bottom = top + voxel_size
        sub_roi = SensibleROI.from_list([left, top, new_right, new_bottom])
        binned_spectrum = self.compute_spectra_for_rolling_sub_roi(roi, sub_roi, step_size)
        return binned_spectrum

    def get_spectrum(self, roi_name: str, mode: SpecType) -> 'np.ndarray':
        """
        Get the spectrum for the given ROI requested by name in the given mode
        """
        if self._stack is None:
            return np.array([])

        roi = self.get_roi(roi_name)
        if mode == SpecType.SAMPLE:
            return self.get_stack_spectrum(self._stack, roi)

        if self._normalise_stack is None:
            return np.array([])

        if mode == SpecType.OPEN:
            return self.get_stack_spectrum(self._normalise_stack, roi)
        elif mode == SpecType.SAMPLE_NORMED:
            if self.normalise_issue():
                return np.array([])
            roi_spectrum = self.get_stack_spectrum(self._stack, roi)
            roi_norm_spectrum = self.get_stack_spectrum(self._normalise_stack, roi)
        return np.divide(roi_spectrum, roi_norm_spectrum, out=np.zeros_like(roi_spectrum), where=roi_norm_spectrum != 0)

    def get_image_shape(self) -> tuple[int, int]:
        if self._stack is not None:
            return self._stack.data.shape[1:]
        else:
            return 0, 0

    def has_stack(self) -> bool:
        """
        Check if data is available to export
        @return: True if data is available to export and False otherwise
        """
        return self._stack is not None

    def save_csv(self, path: Path, normalized: bool) -> None:
        """
        Iterates over all ROIs and saves the spectrum for each one to a CSV file.

        @param path: The path to save the CSV file to.
        @param normalized: Whether to save the normalized spectrum.
        """
        if self._stack is None:
            raise ValueError("No stack selected")

        csv_output = CSVOutput()
        csv_output.add_column("tof_index", np.arange(self._stack.data.shape[0]))

        for roi_name in self.get_list_of_roi_names():
            csv_output.add_column(roi_name, self.get_spectrum(roi_name, SpecType.SAMPLE))
            if normalized:
                if self._normalise_stack is None:
                    raise RuntimeError("No normalisation stack selected")
                csv_output.add_column(roi_name + "_open", self.get_spectrum(roi_name, SpecType.OPEN))
                csv_output.add_column(roi_name + "_norm", self.get_spectrum(roi_name, SpecType.SAMPLE_NORMED))

        with path.open("w") as outfile:
            csv_output.write(outfile)
            self.save_roi_coords(self.get_roi_coords_filename(path))

    def save_rits(self, path: Path, normalized: bool) -> None:
        """
        Saves the spectrum for a specified region of interest (ROI) to a RITS file.

        The method first checks if a stack is selected and if the Time of Flights (ToF) for the sample is available.
        If the 'normalized' parameter is True, it checks if a normalisation stack is selected. If all checks pass,
        it computes the transmission for the ROI and exports the spectrum to a RITS file.

        If a bin and step size are specified, the binned spectrum is computed for the ROI and exports to
        many RITS files, otherwise, it computes a spectrum for the ROI and exports it to a singular RITS file.

        Parameters:
        path (Path): The path where the RITS file will be saved.
        normalized (bool): If True, the method saves the normalized spectrum. If False, it logs an error message.

        Raises:
        ValueError: If no stack is selected or if no ToF for the sample is available.
        RuntimeError: If 'normalized' is True but no normalisation stack is selected.

        Returns:
        None
        """
        if self._stack is None:
            raise ValueError("No stack selected")

        tof = self.get_stack_time_of_flight()
        if tof is None:
            raise ValueError("No Time of Flights for sample. Make sure spectra log has been loaded")

        # RITS expects ToF in μs
        tof *= 1e6

        transmission_error = np.full_like(tof, 0.1)
        if normalized:
            if self._normalise_stack is None:
                raise RuntimeError("No normalisation stack selected")

            if self.bin_size and self.step_size > 0:
                transmission = self.compute_spectra_for_sub_roi(self.get_roi(ROI_RITS), self.bin_size, self.step_size)
            else:
                transmission = self.get_spectrum(ROI_RITS, SpecType.SAMPLE_NORMED)

            self.export_spectrum_to_rits(path, tof, transmission, transmission_error)
        else:
            LOG.error("Data is not normalised to open beam. This will not export to a valid RITS format")

    def get_stack_time_of_flight(self) -> np.array | None:
        if self._stack is None or self._stack.log_file is None:
            return None
        try:
            time_of_flights = self._stack.log_file.get_column(LogColumn.TIME_OF_FLIGHT)
        except KeyError:
            return None
        return np.array(time_of_flights)

    def get_roi_coords_filename(self, path: Path) -> Path:
        """
        Get the path to save the ROI coordinates to.
        @param path: The path to save the CSV file to.
        @return: The path to save the ROI coordinates to.
        """
        return path.with_stem(f"{path.stem}_roi_coords")

    def save_roi_coords(self, path: Path) -> None:
        """
        Save the coordinates of the ROIs to a csv file (ROI name, x_min, x_max, y_min, y_max)
        following Pascal VOC format.
        @param path: The path to save the CSV file to.
        """
        with open(path, encoding='utf-8', mode='w') as f:
            csv_writer = csv.DictWriter(f, fieldnames=["ROI", "X Min", "X Max", "Y Min", "Y Max"])
            csv_writer.writeheader()
            for roi_name, coords in self._roi_ranges.items():
                csv_writer.writerow({
                    "ROI": roi_name,
                    "X Min": coords.left,
                    "X Max": coords.right,
                    "Y Min": coords.top,
                    "Y Max": coords.bottom
                })

    def export_spectrum_to_rits(self, path: Path, tof, transmission, absorption) -> None:
        """
        Export spectrum data to one or many files in RITS format.

        The method checks if the transmission data is binned (i.e., if it is a list of lists).

        If transmission is binned, each spectra within the list is saved in the RITS format in a separate file.
        If not binned, the ToF, transmission and absorption are converted to a RITS formatted data structure and
        then exported to a singular .dat file in RITS format.

        Parameters:
        path (Path): The path where the RITS file will be saved.
        tof: The Time of Flight data for the spectrum.
        transmission: The transmission data for the spectrum. Can be either a list of values or a list of
        lists (for binned data).
        absorption: The absorption data for the spectrum.

        Returns:
        None
        """
        if isinstance(transmission[0], list):
            for i, transmission_spectrum in enumerate(transmission):
                rits_data = saver.create_rits_format(tof, transmission_spectrum, absorption)
                filename = path.with_name(f"{path.stem}_{i}{path.suffix}")
                saver.export_to_dat_rits_format(rits_data, filename)
        else:
            rits_data = saver.create_rits_format(tof, transmission, absorption)
            saver.export_to_dat_rits_format(rits_data, path)

    def remove_roi(self, roi_name) -> None:
        """
        Remove the selected ROI from the model

        @param roi_name: The name of the ROI to remove
        """
        if roi_name in self._roi_ranges.keys():
            if roi_name in self.special_roi_list:
                raise RuntimeError(f"Cannot remove ROI: {roi_name}")
            del self._roi_ranges[roi_name]
        else:
            raise KeyError(
                f"Cannot remove ROI {roi_name} as it does not exist. \n Available ROIs: {self._roi_ranges.keys()}")

    def rename_roi(self, old_name: str, new_name: str) -> None:
        """
        Rename the selected ROI from the model

        @param old_name: The current name of the ROI
        @param new_name: The new name of the ROI
        @raises KeyError: If the ROI does not exist
        @raises RuntimeError: If the ROI is 'all'
        """
        if old_name in self._roi_ranges.keys() and new_name not in self._roi_ranges.keys():
            if old_name in self.special_roi_list:
                raise RuntimeError(f"Cannot remove ROI: {old_name}")
            self._roi_ranges[new_name] = self._roi_ranges.pop(old_name)
        else:
            raise KeyError(f"Cannot rename {old_name} to {new_name} Available:{self._roi_ranges.keys()}")

    def remove_all_roi(self) -> None:
        """
        Remove all ROIs from the model
        """
        self._roi_ranges = {}

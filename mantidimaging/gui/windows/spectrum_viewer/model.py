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


class ErrorMode(Enum):
    STANDARD_DEVIATION = 1
    PROPAGATED = 2


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

    @staticmethod
    def get_stack_spectrum(stack: ImageStack, roi: SensibleROI):
        left, top, right, bottom = roi
        roi_data = stack.data[:, top:bottom, left:right]
        return roi_data.mean(axis=(1, 2))

    @staticmethod
    def get_stack_spectrum_summed(stack: ImageStack, roi: SensibleROI):
        left, top, right, bottom = roi
        roi_data = stack.data[:, top:bottom, left:right]
        return roi_data.sum(axis=(1, 2))

    def normalise_issue(self) -> str:
        if self._stack is None or self._normalise_stack is None:
            return "Need 2 selected stacks"
        if self._stack is self._normalise_stack:
            return "Need 2 different stacks"
        if self._stack.data.shape != self._normalise_stack.data.shape:
            return "Stack shapes must match"
        return ""

    def get_spectrum(self, roi_name: str, mode: SpecType) -> 'np.ndarray':
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

    def get_transmission_error_standard_dev(self, roi_name: str) -> np.ndarray:
        """
        Get the transmission error standard deviation for a given roi
        @param: roi_name The roi name
        @return: a numpy array representing the standard deviation of the transmission
        """
        if self._stack is None or self._normalise_stack is None:
            raise RuntimeError("Sample and open beam must be selected")
        left, top, right, bottom = self.get_roi(roi_name)
        sample = self._stack.data[:, top:bottom, left:right]
        open_beam = self._normalise_stack.data[:, top:bottom, left:right]
        safe_divide = np.divide(sample, open_beam, out=np.zeros_like(sample), where=open_beam != 0)
        return np.std(safe_divide, axis=(1, 2))

    def get_transmission_error_propagated(self, roi_name: str) -> np.ndarray:
        """
        Get the transmission error using propagation of sqrt(n) error for a given roi
        @param: roi_name The roi name
        @return: a numpy array representing the error of the transmission
        """
        if self._stack is None or self._normalise_stack is None:
            raise RuntimeError("Sample and open beam must be selected")
        roi = self.get_roi(roi_name)
        sample = self.get_stack_spectrum_summed(self._stack, roi)
        open_beam = self.get_stack_spectrum_summed(self._normalise_stack, roi)
        error = np.sqrt(sample / open_beam**2 + sample**2 / open_beam**3)
        return error

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

    def save_rits(self, path: Path, normalized: bool, error_mode: ErrorMode) -> None:
        """
        Saves the spectrum for one ROI to a RITS file.

        @param path: The path to save the CSV file to.
        @param normalized: Whether to save the normalized spectrum.
        @param error_mode: Which version (standard deviation or propagated) of the error to use in the RITS export
        """
        if self._stack is None:
            raise ValueError("No stack selected")

        if not normalized or self._normalise_stack is None:
            raise ValueError("Normalisation must be enabled, and a normalise stack must be selected")
        tof = self.get_stack_time_of_flight()
        if tof is None:
            raise ValueError("No Time of Flights for sample. Make sure spectra log has been loaded")

        tof *= 1e6  # RITS expects ToF in μs
        transmission = self.get_spectrum(ROI_RITS, SpecType.SAMPLE_NORMED)

        if error_mode == ErrorMode.STANDARD_DEVIATION:
            transmission_error = self.get_transmission_error_standard_dev(ROI_RITS)
        elif error_mode == ErrorMode.PROPAGATED:
            transmission_error = self.get_transmission_error_propagated(ROI_RITS)
        else:
            raise ValueError("Invalid error_mode given")

        self.export_spectrum_to_rits(path, tof, transmission, transmission_error)

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
        Export spectrum to RITS format
        """
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

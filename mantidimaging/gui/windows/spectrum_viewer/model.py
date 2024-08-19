# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import csv
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from functools import lru_cache

import numpy as np
from math import ceil
import dask.array as da
from dask import delayed

from logging import getLogger
from mantidimaging.core.data import ImageStack
from mantidimaging.core.io.csv_output import CSVOutput
from mantidimaging.core.io import saver
from mantidimaging.core.io.instrument_log import LogColumn
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.unit_conversion import UnitConversion

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.presenter import SpectrumViewerWindowPresenter

LOG = getLogger(__name__)

ROI_ALL = "all"
ROI_RITS = "rits_roi"


class SpecType(Enum):
    SAMPLE = 1
    OPEN = 2
    SAMPLE_NORMED = 3


class ToFUnitMode(Enum):
    IMAGE_NUMBER = 1
    TOF_US = 2
    WAVELENGTH = 3
    ENERGY = 4


class ErrorMode(Enum):
    STANDARD_DEVIATION = "Standard Deviation"
    PROPAGATED = "Propagated"

    @classmethod
    def get_by_value(cls, value: str) -> ErrorMode:
        for element in cls:
            if element.value == value:
                return element
        raise ValueError(f"Unknown error mode: {value}")


class SpectrumViewerWindowModel:
    """
    The model for the spectrum viewer window.
    This model is responsible for storing the state of the window and providing
    the presenter with the data it needs to update the view.
    The model is also responsible for saving ROI data to a csv file.
    """
    presenter: SpectrumViewerWindowPresenter
    _stack: ImageStack | None = None
    _normalise_stack: ImageStack | None = None
    tof_range: tuple[int, int] = (0, 0)
    tof_plot_range: tuple[float, float] | tuple[int, int] = (0, 0)
    _roi_ranges: dict[str, SensibleROI]
    tof_mode: ToFUnitMode
    tof_data: np.ndarray | None = None
    tof_range_full: tuple[int, int] = (0, 0)

    def __init__(self, presenter: SpectrumViewerWindowPresenter):
        self._cache = {}

        self.presenter = presenter
        self._roi_id_counter = 0
        self._roi_ranges = {}
        self.special_roi_list = [ROI_ALL]

        self.tof_data = self.get_stack_time_of_flight()
        if self.tof_data is None:
            self.tof_mode = ToFUnitMode.IMAGE_NUMBER
        else:
            self.tof_mode = ToFUnitMode.WAVELENGTH

        self.units = UnitConversion()

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

    def set_stack(self, stack: ImageStack | None) -> None:
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
        self.tof_range_full = self.tof_range
        self.tof_data = self.get_stack_time_of_flight()
        self.set_new_roi(ROI_ALL)

    def set_new_roi(self, name: str) -> None:
        """
        Sets a new ROI with the given name

        @param name: The name of the new ROI
        """
        height, width = self.get_image_shape()
        self.set_roi(name, SensibleROI.from_list([0, 0, width, height]))

    def set_normalise_stack(self, normalise_stack: ImageStack | None) -> None:
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

    def get_averaged_image(self) -> np.ndarray | None:
        """
        Get the averaged image from the stack in the model returning as a numpy array
        or None if it does not
        """
        if self._stack is not None:
            tof_slice = slice(self.tof_range[0], self.tof_range[1] + 1)
            return self._stack.data[tof_slice].mean(axis=0)
        return None

    @staticmethod
    def get_stack_spectrum(stack: ImageStack | None, roi: SensibleROI):
        if stack is None:
            return da.array([])
        left, top, right, bottom = roi
        roi_data = da.from_array(stack.data[:, top:bottom, left:right], chunks='auto')
        return roi_data.mean(axis=(1, 2))

    @staticmethod
    def get_stack_spectrum_summed(stack: ImageStack, roi: SensibleROI):
        left, top, right, bottom = roi
        roi_data = da.from_array(stack.data[:, top:bottom, left:right], chunks='auto')
        return roi_data.sum(axis=(1, 2))

    def normalise_issue(self) -> str:
        if self._stack is None or self._normalise_stack is None:
            return "Need 2 selected stacks"
        if self._stack is self._normalise_stack:
            return "Need 2 different stacks"
        if self._stack.data.shape != self._normalise_stack.data.shape:
            return "Stack shapes must match"
        return ""

    @lru_cache(maxsize=128)
    def get_spectrum(self,
                     roi: str | SensibleROI,
                     mode: SpecType,
                     normalise_with_shuttercount: bool = False) -> np.ndarray:
        if self._stack is None:
            return np.array([])

        if isinstance(roi, str):
            roi = self.get_roi(roi)

        roi_key = self.roi_to_key(roi)
        cache_key = (roi_key, mode, normalise_with_shuttercount)

        if cache_key in self._cache:
            return self._cache[cache_key]

        spectrum = self.compute_full_spectrum(roi, mode)

        if normalise_with_shuttercount:
            spectrum = self.normalize_with_shuttercount(spectrum)

        self._cache[cache_key] = spectrum
        return spectrum

    def normalize_with_shuttercount(self, spectrum):
        average_shuttercount = self.get_shuttercount()
        return spectrum / average_shuttercount if average_shuttercount != 0 else np.zeros_like(spectrum)

    def compute_full_spectrum(self, roi, mode):
        mode_operations = {
            SpecType.SAMPLE: lambda: self.get_stack_spectrum(self._stack, roi),
            SpecType.OPEN: lambda: self.get_stack_spectrum(self.normalize_stack, roi),
            SpecType.SAMPLE_NORMED: lambda: self.compute_normalized_spectrum(roi)
        }

        if mode not in mode_operations:
            raise ValueError(f"Unsupported mode: {mode}")

        return mode_operations[mode]().compute()

    def compute_normalized_spectrum(self, roi):
        roi_spectrum = self.get_stack_spectrum(self._stack, roi)
        roi_norm_spectrum = self.get_stack_spectrum(self.normalize_stack, roi)
        return da.divide(roi_spectrum, roi_norm_spectrum, out=da.zeros_like(roi_spectrum), where=roi_norm_spectrum != 0)

    def update_spectrum(self, old_roi, new_roi):
        if self.can_incrementally_update(old_roi, new_roi):
            removed_data, added_data = self.calculate_data_differences(old_roi, new_roi)
            return self.update_spectrum_incrementally(removed_data, added_data)
        else:
            return self.get_spectrum(new_roi, self.spectrum_mode)

    def calculate_data_differences(self, old_roi, new_roi):
        intersection = old_roi.intersection(new_roi)
        removed_data_mask, added_data_mask = self._create_masks(old_roi, new_roi, intersection)
        removed_data = self.extract_data(self._stack, old_roi, removed_data_mask)
        added_data = self.extract_data(self._stack, new_roi, added_data_mask)
        return removed_data, added_data

    def _create_masks(self, old_roi, new_roi, intersection):
        removed_data_mask = np.ones((old_roi.height, old_roi.width), dtype=bool)
        added_data_mask = np.zeros((new_roi.height, new_roi.width), dtype=bool)

        if intersection:
            self.apply_mask(removed_data_mask, old_roi, intersection, negate=True)
            self.apply_mask(added_data_mask, new_roi, intersection, negate=False)

        return removed_data_mask, added_data_mask

    def apply_mask(self, mask, roi, intersection, negate=False):
        offset_x1 = max(0, intersection.left - roi.left)
        offset_y1 = max(0, intersection.top - roi.top)
        offset_x2 = min(roi.width, intersection.right - roi.left)
        offset_y2 = min(roi.height, intersection.bottom - roi.top)

        mask[offset_y1:offset_y2, offset_x1:offset_x2] = not negate

    def extract_data(self, stack, roi, mask):
        if not stack:
            return da.array([])

        data = da.from_array(stack.data[:, roi.top:roi.bottom, roi.left:roi.right], chunks='auto')
        return data[mask].compute()

    def update_spectrum_incrementally(self, removed_data, added_data):
        if removed_data.size > 0:
            self.old_spectrum -= removed_data.sum(axis=0)

        if added_data.size > 0:
            self.old_spectrum += added_data.sum(axis=0)

        return self.old_spectrum

    def can_incrementally_update(self, old_roi, new_roi):
        max_shift_allowed = 10
        return all([
            abs(new_roi.left - old_roi.left) <= max_shift_allowed,
            abs(new_roi.top - old_roi.top) <= max_shift_allowed,
            abs((new_roi.right - new_roi.left) - (old_roi.right - old_roi.left)) <= max_shift_allowed,
            abs((new_roi.bottom - new_roi.top) - (old_roi.bottom - old_roi.top)) <= max_shift_allowed,
            old_roi.has_significant_overlap(new_roi, threshold=0.5)
        ])

    def roi_to_key(self, roi):
        if isinstance(roi, SensibleROI):
            return (roi.left, roi.top, roi.right, roi.bottom)
        return roi

    def clear_cache(self):
        self._cache.clear()

    def get_transmission_error_standard_dev(self, roi: SensibleROI) -> np.ndarray:
        """
        Get the transmission error standard deviation for a given roi
        @param: roi_name The roi name
        @return: a numpy array representing the standard deviation of the transmission
        """
        if self._stack is None or self._normalise_stack is None:
            raise RuntimeError("Sample and open beam must be selected")
        left, top, right, bottom = roi
        sample = self._stack.data[:, top:bottom, left:right]
        open_beam = self._normalise_stack.data[:, top:bottom, left:right]
        safe_divide = np.divide(sample, open_beam, out=np.zeros_like(sample), where=open_beam != 0)
        return np.std(safe_divide, axis=(1, 2))

    def get_transmission_error_propagated(self, roi: SensibleROI) -> np.ndarray:
        """
        Get the transmission error using propagation of sqrt(n) error for a given roi
        @param: roi_name The roi name
        @return: a numpy array representing the error of the transmission
        """
        if self._stack is None or self._normalise_stack is None:
            raise RuntimeError("Sample and open beam must be selected")
        sample = self.get_stack_spectrum_summed(self._stack, roi)
        open_beam = self.get_stack_spectrum_summed(self._normalise_stack, roi)
        error = np.sqrt(sample / open_beam**2 + sample**2 / open_beam**3)
        return error

    def get_image_shape(self) -> tuple[int, int]:
        if self._stack is not None:
            assert len(self._stack.data.shape) == 3
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

    def save_single_rits_spectrum(self, path: Path, error_mode: ErrorMode) -> None:
        """
        Saves the spectrum for the RITS ROI to a RITS file.

        @param path: The path to save the CSV file to.
        @param normalized: Whether to save the normalized spectrum.
        @param error_mode: Which version (standard deviation or propagated) of the error to use in the RITS export
        """
        self.save_rits_roi(path, error_mode, self.get_roi(ROI_RITS))

    def save_rits_roi(self, path: Path, error_mode: ErrorMode, roi: SensibleROI) -> None:
        """
        Saves the spectrum for one ROI to a RITS file.

        @param path: The path to save the CSV file to.
        @param error_mode: Which version (standard deviation or propagated) of the error to use in the RITS export
        """
        if self._stack is None:
            raise ValueError("No stack selected")

        if self._normalise_stack is None:
            raise ValueError("A normalise stack must be selected")
        tof = self.get_stack_time_of_flight()
        if tof is None:
            raise ValueError("No Time of Flights for sample. Make sure spectra log has been loaded")

        tof *= 1e6  # RITS expects ToF in μs
        transmission = self.get_spectrum(roi, SpecType.SAMPLE_NORMED)

        if error_mode == ErrorMode.STANDARD_DEVIATION:
            transmission_error = self.get_transmission_error_standard_dev(roi)
        elif error_mode == ErrorMode.PROPAGATED:
            transmission_error = self.get_transmission_error_propagated(roi)
        else:
            raise ValueError("Invalid error_mode given")

        self.export_spectrum_to_rits(path, tof, transmission, transmission_error)

    def validate_bin_and_step_size(self, roi, bin_size: int, step_size: int) -> None:
        """
        Validates the bin size and step size for saving RITS images.
        This method checks the following conditions:
        - Both bin size and step size must be greater than 0.
        - Bin size must be larger than or equal to step size.
        - Both bin size and step size must be less than or equal to the smallest dimension of the ROI.
        If any of these conditions are not met, a ValueError is raised.
        Parameters:
            roi: The region of interest (ROI) to which the bin size and step size should be compared.
            bin_size (int): The size of the bins to be validated.
            step_size (int): The size of the steps to be validated.
        Raises:
            ValueError: If any of the validation conditions are not met.
        """
        if bin_size and step_size < 1:
            raise ValueError("Both bin size and step size must be greater than 0")
        if bin_size <= step_size:
            raise ValueError("Bin size must be larger than or equal to step size")
        if bin_size and step_size > min(roi.width, roi.height):
            raise ValueError("Both bin size and step size must be less than or equal to the ROI size")

    def save_rits_images(self,
                         directory: Path,
                         error_mode: ErrorMode,
                         bin_size: int,
                         step: int,
                         progress: Progress | None = None) -> None:
        """
        Saves multiple Region of Interest (ROI) images to RITS files.

        This method divides the ROI into multiple sub-regions of size 'bin_size' and saves each sub-region
        as a separate RITS image.
        The sub-regions are created by sliding a window of size 'bin_size' across the ROI with a step size of 'step'.

        During each iteration on a given axis by the step size, a check is made to see if
        the sub_roi has reached the end of the ROI on that axis and if so, the iteration for that axis is stopped.


        Parameters:
        directory (Path): The directory where the RITS images will be saved. If None, no images will be saved.
        normalised (bool): If True, the images will be normalised.
        error_mode (ErrorMode): The error mode to use when saving the images.
        bin_size (int): The size of the sub-regions.
        step (int): The step size to use when sliding the window across the ROI.

        Returns:
        None
        """
        roi = self.get_roi(ROI_RITS)
        left, top, right, bottom = roi
        x_iterations = min(ceil((right - left) / step), ceil((right - left - bin_size) / step) + 1)
        y_iterations = min(ceil((bottom - top) / step), ceil((bottom - top - bin_size) / step) + 1)
        progress = Progress.ensure_instance(progress, num_steps=x_iterations * y_iterations)

        self.validate_bin_and_step_size(roi, bin_size, step)
        for y in range(y_iterations):
            sub_top = top + y * step
            sub_bottom = min(sub_top + bin_size, bottom)
            for x in range(x_iterations):
                sub_left = left + x * step
                sub_right = min(sub_left + bin_size, right)
                sub_roi = SensibleROI.from_list([sub_left, sub_top, sub_right, sub_bottom])
                path = directory / f"rits_image_{x}_{y}.dat"
                self.save_rits_roi(path, error_mode, sub_roi)
                progress.update()
                if sub_right == right:
                    break
            if sub_bottom == bottom:
                break

    def get_stack_time_of_flight(self) -> np.ndarray | None:
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

    def set_relevant_tof_units(self) -> None:
        if self._stack is not None:
            self.tof_data = self.get_stack_time_of_flight()
            if self.tof_mode == ToFUnitMode.IMAGE_NUMBER or self.tof_data is None:
                self.tof_plot_range = (0, self._stack.data.shape[0] - 1)
                self.tof_range = (0, self._stack.data.shape[0] - 1)
                self.tof_data = np.arange(self.tof_range[0], self.tof_range[1] + 1)
            else:
                self.units.set_data_to_convert(self.tof_data)
                if self.tof_mode == ToFUnitMode.TOF_US:
                    self.tof_data = self.units.tof_seconds_to_us()
                elif self.tof_mode == ToFUnitMode.WAVELENGTH:
                    self.tof_data = self.units.tof_seconds_to_wavelength_in_angstroms()
                elif self.tof_mode == ToFUnitMode.ENERGY:
                    self.tof_data = self.units.tof_seconds_to_energy()
                self.tof_plot_range = (self.tof_data.min(), self.tof_data.max())
                self.tof_range = (0, self.tof_data.size)

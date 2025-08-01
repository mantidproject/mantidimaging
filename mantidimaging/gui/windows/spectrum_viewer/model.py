# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import csv
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, Final

import numpy as np
from math import ceil

from logging import getLogger
from mantidimaging.core.data.imagestack import ImageStack
from mantidimaging.core.fitting.fitting_engine import FittingEngine
from mantidimaging.core.fitting.fitting_functions import ErfStepFunction
from mantidimaging.core.io.csv_output import CSVOutput
from mantidimaging.core.io import saver
from mantidimaging.core.io.instrument_log import LogColumn, ShutterCountColumn
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.unit_conversion import UnitConversion

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.presenter import SpectrumViewerWindowPresenter

LOG = getLogger(__name__)

ROI_RITS: Final = "rits_roi"


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


class AllowedModesTypedDict(TypedDict):
    mode: ToFUnitMode
    label: str


allowed_modes: dict[str, AllowedModesTypedDict] = {
    "Image Index": {
        "mode": ToFUnitMode.IMAGE_NUMBER,
        "label": "Image index"
    },
    "Wavelength": {
        "mode": ToFUnitMode.WAVELENGTH,
        "label": "Neutron Wavelength (\u212B)"
    },
    "Energy": {
        "mode": ToFUnitMode.ENERGY,
        "label": "Neutron Energy (MeV)"
    },
    "Time of Flight (\u03BCs)": {
        "mode": ToFUnitMode.TOF_US,
        "label": "Time of Flight (\u03BCs)"
    }
}


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
    tof_mode: ToFUnitMode = ToFUnitMode.WAVELENGTH
    tof_data: np.ndarray = np.array([])
    spectrum_cache: dict[tuple, np.ndarray] = {}

    def __init__(self, presenter: SpectrumViewerWindowPresenter):
        self.presenter = presenter
        self._roi_id_counter = 0

        self.units = UnitConversion()

        self.fitting_engine = FittingEngine(ErfStepFunction())

    def roi_name_generator(self) -> str:
        """
        Returns a new Unique ID for newly created ROIs

        :return: A new unique ID
        """
        new_name = f"roi_{self._roi_id_counter}" if self._roi_id_counter > 0 else "roi"
        self._roi_id_counter += 1
        return new_name

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
        self.tof_range = (0, stack.data.shape[0] - 1)
        self.tof_data = self.get_stack_time_of_flight()
        LOG.info("Sample stack set: shape=%s, ToF range=(%d–%d)", stack.data.shape, self.tof_range[0],
                 self.tof_range[1])

    def set_normalise_stack(self, normalise_stack: ImageStack | None) -> None:
        self._normalise_stack = normalise_stack
        if normalise_stack is not None:
            LOG.info("Normalisation stack set: shape=%s", normalise_stack.data.shape)
        else:
            LOG.info("Normalisation stack cleared")

    def get_normalized_averaged_image(self) -> np.ndarray | None:
        """
        Get the normalized averaged image if both sample and normalization stacks are available.
        """
        if self._stack is None or self._normalise_stack is None:
            return None

        tof_slice = slice(self.tof_range[0], self.tof_range[1] + 1)
        sample_data = self._stack.data[tof_slice].mean(axis=0)
        norm_data = self._normalise_stack.data[tof_slice].mean(axis=0)
        normalized_image = np.divide(sample_data, norm_data, out=np.zeros_like(sample_data), where=norm_data != 0)
        shutter_correction = self.get_shuttercount_normalised_correction_parameter()
        normalized_image /= shutter_correction
        return normalized_image

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
    def get_stack_spectrum(stack: ImageStack | None,
                           roi: SensibleROI,
                           chunk_start: int = 0,
                           chunk_end: int | None = None) -> np.ndarray:
        """
        Computes the mean spectrum of the given image stack within the specified region of interest (ROI).
        If the image stack is None, an empty numpy array is returned.
        Parameters:
            stack (Optional[ImageStack]): The image stack to compute the spectrum from.
                It can be None, in which case an empty array is returned.
            roi (SensibleROI): The region of interest within the image stack.
                It is a tuple or list of four integers specifying the left, top, right, and bottom coordinates.
        Returns:
            numpy.ndarray: The mean spectrum of the image stack within the ROI.
                It is a 1D array where each element is the mean of the corresponding layer of the stack within the ROI.
        """
        if stack is None:
            return np.array([])
        left, top, right, bottom = roi
        roi_data = stack.data[chunk_start:chunk_end, top:bottom, left:right]
        return roi_data.mean(axis=(1, 2))

    @staticmethod
    def get_stack_spectrum_summed(stack: ImageStack, roi: SensibleROI) -> np.ndarray:
        left, top, right, bottom = roi
        roi_data = stack.data[:, top:bottom, left:right]
        return roi_data.sum(axis=(1, 2))

    def get_number_of_images_in_stack(self) -> int:
        if self._stack is not None:
            return self._stack.data.shape[0]
        else:
            return 0

    def normalise_issue(self) -> str:
        if self._stack is None or self._normalise_stack is None:
            return "Need 2 selected stacks"
        if self._stack is self._normalise_stack:
            return "Need 2 different stacks"
        if self._stack.data.shape != self._normalise_stack.data.shape:
            return "Stack shapes must match"
        return ""

    def shuttercount_issue(self) -> str:
        """
        Return an error message if there is an issue with the shutter count data.
        """
        assert self._stack and self._normalise_stack
        if not self._stack.shutter_count_file or not self._normalise_stack.shutter_count_file:
            return "Need 2 selected ShutterCount stacks"
        if self._stack.shutter_count_file.data == self._normalise_stack.shutter_count_file.data:
            return "Need 2 different ShutterCount stacks"
        return ""

    def get_spectrum(self,
                     roi: SensibleROI,
                     mode: SpecType,
                     normalise_with_shuttercount: bool = False,
                     chunk_start: int = 0,
                     chunk_end: int | None = None) -> np.ndarray:
        if (*roi, mode, normalise_with_shuttercount) in self.spectrum_cache.keys():
            return self.spectrum_cache[(*roi, mode, normalise_with_shuttercount)]

        if self._stack is None:
            return np.array([])

        if self.presenter.initial_sample_change:
            return np.zeros(self._stack.data.shape[0])

        if mode == SpecType.SAMPLE:
            sample_spectrum = self.get_stack_spectrum(self._stack, roi, chunk_start, chunk_end)
            return sample_spectrum

        if self._normalise_stack is None:
            return np.array([])

        if mode == SpecType.OPEN:
            open_spectrum = self.get_stack_spectrum(self._normalise_stack, roi, chunk_start, chunk_end)
            return open_spectrum
        elif mode == SpecType.SAMPLE_NORMED:
            if self.normalise_issue():
                return np.array([])
            roi_spectrum = self.get_stack_spectrum(self._stack, roi, chunk_start, chunk_end)
            roi_norm_spectrum = self.get_stack_spectrum(self._normalise_stack, roi, chunk_start, chunk_end)
        spectrum = np.divide(roi_spectrum,
                             roi_norm_spectrum,
                             out=np.zeros_like(roi_spectrum),
                             where=roi_norm_spectrum != 0)
        if normalise_with_shuttercount:
            average_shuttercount = self.get_shuttercount_normalised_correction_parameter()
            spectrum = spectrum / average_shuttercount

        LOG.debug("Computing spectrum: ROI=%s, mode=%s, cached=%s", roi, mode.name,
                  (*roi, mode, normalise_with_shuttercount) in self.spectrum_cache)

        return spectrum

    def store_spectrum(self, roi: SensibleROI, mode: SpecType, normalise_with_shuttercount: bool, spectrum: np.ndarray):
        params = (*roi, mode, normalise_with_shuttercount)
        if len(self.spectrum_cache) > 99:
            full_width, full_height = self.get_image_shape()
            full_size = (0, 0, full_width, full_height)
            for param_to_evict in self.spectrum_cache.keys():
                if param_to_evict[:4] != full_size:
                    break
            self.spectrum_cache.pop(param_to_evict)
        self.spectrum_cache[params] = spectrum

    def get_shuttercount_normalised_correction_parameter(self) -> float:
        """
        Normalize ShutterCount values and return only the initial normalized value.
        We normalise all values to future proof against normalizing against all available ShutterCount
        values should we find the initial value is not sufficient.
        """
        sample_shuttercount = self.get_stack_shuttercounts(self._stack)
        open_shuttercount = self.get_stack_shuttercounts(self._normalise_stack)
        if sample_shuttercount is None or open_shuttercount is None:
            return 1.0  # No shutter count data available so no correction needed
        normalised_shuttercounts = np.divide(sample_shuttercount.astype(np.float32),
                                             open_shuttercount.astype(np.float32),
                                             out=np.ones_like(sample_shuttercount, dtype=np.float32),
                                             where=open_shuttercount != 0)
        return normalised_shuttercounts[0]

    def get_stack_shuttercounts(self, stack: ImageStack | None) -> np.ndarray | None:
        if stack is None or stack.shutter_count_file is None:
            return None
        try:
            shutter_counts = stack.shutter_count_file.get_column(ShutterCountColumn.SHUTTER_COUNT)
        except KeyError:
            return None
        return np.array(shutter_counts)

    def get_transmission_error_standard_dev(self,
                                            roi: SensibleROI,
                                            normalise_with_shuttercount: bool = False) -> np.ndarray:
        """
        Get the transmission error standard deviation for a given roi
        @param: roi_name The roi name
        @param: normalised Default is True. If False, the normalization is not applied
        @return: a numpy array representing the standard deviation of the transmission
        """
        if self._stack is None or self._normalise_stack is None:
            raise RuntimeError("Sample and open beam must be selected")
        left, top, right, bottom = roi
        sample = self._stack.data[:, top:bottom, left:right]
        open_beam = self._normalise_stack.data[:, top:bottom, left:right]
        safe_divide = np.divide(sample, open_beam, out=np.zeros_like(sample), where=open_beam != 0)
        if normalise_with_shuttercount:
            average_shuttercount = self.get_shuttercount_normalised_correction_parameter()
            safe_divide = safe_divide / average_shuttercount

        return np.std(safe_divide, axis=(1, 2))

    def get_transmission_error_propagated(self,
                                          roi: SensibleROI,
                                          normalise_with_shuttercount: bool = False) -> np.ndarray:
        """
        Get the transmission error using propagation of sqrt(n) error for a given roi
        @param: roi_name The roi name
        @param: normalised Default is True. If False, the normalization is not applied
        @return: a numpy array representing the error of the transmission
        """
        if self._stack is None or self._normalise_stack is None:
            raise RuntimeError("Sample and open beam must be selected")
        sample = self.get_stack_spectrum_summed(self._stack, roi)
        open_beam = self.get_stack_spectrum_summed(self._normalise_stack, roi)
        error = np.sqrt(sample / open_beam**2 + sample**2 / open_beam**3)

        if normalise_with_shuttercount:
            average_shuttercount = self.get_shuttercount_normalised_correction_parameter()
            error = error / average_shuttercount
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

    def save_csv(self,
                 path: Path,
                 rois: dict[str, SensibleROI],
                 normalise: bool,
                 normalise_with_shuttercount: bool = False) -> None:
        """
        Iterates over all ROIs and saves the spectrum for each one to a CSV file.
        @param path: The path to save the CSV file to.
        @param normalized: Whether to save the normalized spectrum.
        """
        if self._stack is None:
            raise ValueError("No stack selected")
        if not rois:
            raise ValueError("No ROIs provided")

        csv_output = CSVOutput()
        csv_output.add_column("ToF_index", np.arange(self._stack.data.shape[0]), "Index")

        local_tof_data = self.get_stack_time_of_flight()
        if local_tof_data.size != 0:
            self.units.set_data_to_convert(local_tof_data)
            csv_output.add_column("Wavelength", self.units.tof_seconds_to_wavelength_in_angstroms(), "Angstrom")
            csv_output.add_column("ToF", self.units.tof_seconds_to_us(), "Microseconds")
            csv_output.add_column("Energy", self.units.tof_seconds_to_energy(), "MeV")
        for roi_name, roi in rois.items():
            csv_output.add_column(roi_name, self.get_spectrum(roi, SpecType.SAMPLE, normalise_with_shuttercount),
                                  "Counts")
            if normalise:
                if self._normalise_stack is None:
                    raise RuntimeError("No normalisation stack selected")
                csv_output.add_column(f"{roi_name}_open", self.get_spectrum(roi, SpecType.OPEN), "Counts")
                csv_output.add_column(f"{roi_name}_norm",
                                      self.get_spectrum(roi, SpecType.SAMPLE_NORMED, normalise_with_shuttercount),
                                      "Counts")

        with path.open("w") as outfile:
            csv_output.write(outfile)
            self.save_roi_coords(self.get_roi_coords_filename(path), rois)

        LOG.info("Saving spectra to CSV: path=%s, ROIs=%s, normalised=%s, shuttercount=%s", path, list(rois.keys()),
                 normalise, normalise_with_shuttercount)

    def save_single_rits_spectrum(self, path: Path, error_mode: ErrorMode, roi: SensibleROI) -> None:
        """
        Saves the spectrum for the RITS ROI to a RITS file.

        @param path: The path to save the CSV file to.
        @param error_mode: Which version (standard deviation or propagated) of the error to use in the RITS export.
        """
        self.save_rits_roi(path, error_mode, roi)

    def save_rits_roi(self, path: Path, error_mode: ErrorMode, roi: SensibleROI, normalise: bool = False) -> None:
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
        if tof.size == 0:
            raise ValueError("No Time of Flights for sample. Make sure spectra log has been loaded")

        tof *= 1e6  # RITS expects ToF in μs
        transmission = self.get_spectrum(roi, SpecType.SAMPLE_NORMED, normalise)

        if error_mode == ErrorMode.STANDARD_DEVIATION:
            transmission_error = self.get_transmission_error_standard_dev(roi, normalise)
        elif error_mode == ErrorMode.PROPAGATED:
            transmission_error = self.get_transmission_error_propagated(roi, normalise)
        else:
            raise ValueError("Invalid error_mode given")

        self.export_spectrum_to_rits(path, tof, transmission, transmission_error)

        LOG.info("Exporting RITS file: path=%s, ROI=(%d,%d,%d,%d), error_mode=%s", path, roi.left, roi.top, roi.right,
                 roi.bottom, error_mode.name)

    def validate_bin_and_step_size(self, roi: SensibleROI, bin_size: int, step_size: int) -> None:
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
        if bin_size < step_size:
            raise ValueError("Bin size must be larger than or equal to step size")
        if bin_size and step_size > min(roi.width, roi.height):
            raise ValueError("Both bin size and step size must be less than or equal to the ROI size")

    def save_rits_images(self,
                         directory: Path,
                         error_mode: ErrorMode,
                         bin_size: int,
                         step: int,
                         roi: SensibleROI,
                         normalise: bool = False,
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
        roi (SensibleROI): The parent ROI to be subdivided.
        normalise (bool): If True, the images will be normalised.
        progress (Progress | None): Optional progress reporter.

        Returns:
        None
        """
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
                self.save_rits_roi(path, error_mode, sub_roi, normalise)
                progress.update()
                if sub_right == right:
                    break
            if sub_bottom == bottom:
                break

    def get_stack_time_of_flight(self) -> np.ndarray:
        if self._stack is None or self._stack.log_file is None:
            return np.array([])
        try:
            time_of_flights = self._stack.log_file.get_column(LogColumn.TIME_OF_FLIGHT)
        except KeyError:
            return np.array([])
        return np.array(time_of_flights)

    def get_roi_coords_filename(self, path: Path) -> Path:
        """
        Get the path to save the ROI coordinates to.
        @param path: The path to save the CSV file to.
        @return: The path to save the ROI coordinates to.
        """
        return path.with_stem(f"{path.stem}_roi_coords")

    def save_roi_coords(self, path: Path, rois: dict[str, SensibleROI]) -> None:
        with open(path, encoding='utf-8', mode='w') as f:
            csv_writer = csv.DictWriter(f, fieldnames=["ROI", "X Min", "X Max", "Y Min", "Y Max"])
            csv_writer.writeheader()
            for roi_name, coords in rois.items():
                csv_writer.writerow({
                    "ROI": roi_name,
                    "X Min": coords.left,
                    "X Max": coords.right,
                    "Y Min": coords.top,
                    "Y Max": coords.bottom,
                })

    def export_spectrum_to_rits(self, path: Path, tof: np.ndarray, transmission: np.ndarray,
                                absorption: np.ndarray) -> None:
        """
        Export spectrum to RITS format
        """
        rits_data = saver.create_rits_format(tof, transmission, absorption)
        saver.export_to_dat_rits_format(rits_data, path)

    def remove_all_roi(self) -> None:
        """
        Remove all ROIs from the model
        """
        self._roi_id_counter = 0

    def set_relevant_tof_units(self) -> None:
        if self._stack is not None:
            self.tof_data = self.get_stack_time_of_flight()
            if self.tof_mode == ToFUnitMode.IMAGE_NUMBER or self.tof_data.size == 0:
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

    def set_tof_unit_mode_for_stack(self) -> None:
        if self.get_stack_time_of_flight().size == 0 or self.tof_data.size == 0:
            self.tof_mode = ToFUnitMode.IMAGE_NUMBER
            self.presenter.change_selected_menu_option("Image Index")
        elif self.tof_mode == ToFUnitMode.ENERGY:
            self.presenter.change_selected_menu_option("Energy")
        elif self.tof_mode == ToFUnitMode.TOF_US:
            self.presenter.change_selected_menu_option("Time of Flight (\u03BCs)")
        else:
            self.tof_mode = ToFUnitMode.WAVELENGTH
            self.presenter.change_selected_menu_option("Wavelength")

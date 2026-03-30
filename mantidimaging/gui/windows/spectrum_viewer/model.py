# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import csv
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, Final

import numpy as np

from logging import getLogger
from mantidimaging.core.data.imagestack import ImageStack
from mantidimaging.core.fitting.fitting_engine import FittingEngine, BoundType
from mantidimaging.core.fitting.fitting_functions import ErfStepFunction, FittingRegion
from mantidimaging.core.io.csv_output import CSVOutput
from mantidimaging.core.io import saver
from mantidimaging.core.io.instrument_log import LogColumn, ShutterCountColumn
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.unit_conversion import UnitConversion

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.presenter import SpectrumViewerWindowPresenter, SpectrumFitResult
    from mantidimaging.core.utility.sensible_roi import SensibleROI, ROIBinner

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


class ColourRangeMode(Enum):
    IQR = "1.5\u00d7IQR"
    MAD = "Median \u00b13\u00d7MAD"
    PERCENTILE = "2nd - 98th %ile"


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
        self.fit_results: list[tuple[str, SpectrumFitResult]] | None = None
        self._good_fits_by_roi_name: dict[str, SpectrumFitResult] = {}
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
        self.tof_range = (0, stack.shape[0] - 1)
        self.tof_data = self.get_stack_time_of_flight()
        LOG.info("Sample stack set: shape=%s, ToF range=(%d–%d)", stack.shape, self.tof_range[0], self.tof_range[1])

    def set_normalise_stack(self, normalise_stack: ImageStack | None) -> None:
        self._normalise_stack = normalise_stack
        if normalise_stack is not None:
            LOG.info("Normalisation stack set: shape=%s", normalise_stack.shape)
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
            return self._stack.shape[0]
        else:
            return 0

    def normalise_issue(self) -> str:
        if self._stack is None or self._normalise_stack is None:
            return "Need 2 selected stacks"
        if self._stack is self._normalise_stack:
            return "Need 2 different stacks"
        if self._stack.shape != self._normalise_stack.shape:
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
                     chunk_end: int | None = None,
                     open_beam_roi: SensibleROI | None = None) -> np.ndarray:

        open_beam_roi = open_beam_roi or roi
        cache_key = (*roi, *open_beam_roi, mode, normalise_with_shuttercount)
        if cache_key in self.spectrum_cache and chunk_start == 0 and chunk_end is None:
            LOG.debug("Using cached spectrum: ROI=%s, Open ROI=%s, mode=%s", roi, open_beam_roi, mode.name)
            return self.spectrum_cache[cache_key]

        spectrum = self._compute_spectrum(roi, mode, normalise_with_shuttercount, chunk_start, chunk_end, open_beam_roi)
        spectrum = np.asarray(spectrum)

        if chunk_start == 0 and chunk_end is None:
            self.store_spectrum(roi, mode, normalise_with_shuttercount, spectrum, open_beam_roi=open_beam_roi)
            LOG.debug("Stored spectrum cache: ROI=%s, Open ROI=%s, mode=%s", roi, open_beam_roi, mode.name)

        return spectrum

    def _compute_spectrum(self,
                          roi: SensibleROI,
                          mode: SpecType,
                          normalise_with_shuttercount: bool = False,
                          chunk_start: int = 0,
                          chunk_end: int | None = None,
                          open_beam_roi: SensibleROI | None = None) -> np.ndarray:

        if self._stack is None:
            return np.array([])
        open_beam_roi = open_beam_roi or roi
        if mode == SpecType.SAMPLE:
            sample_spectrum = self.get_stack_spectrum(self._stack, roi, chunk_start, chunk_end)
            return sample_spectrum
        if self._normalise_stack is None:
            return np.array([])
        if mode == SpecType.OPEN:
            open_spectrum = self.get_stack_spectrum(self._normalise_stack, open_beam_roi, chunk_start, chunk_end)
            return open_spectrum
        elif mode == SpecType.SAMPLE_NORMED:
            if self.normalise_issue():
                return np.array([])
        roi_spectrum = self.get_stack_spectrum(self._stack, roi, chunk_start, chunk_end)
        roi_norm_spectrum = self.get_stack_spectrum(self._normalise_stack, open_beam_roi, chunk_start, chunk_end)
        spectrum = np.divide(roi_spectrum,
                             roi_norm_spectrum,
                             out=np.zeros_like(roi_spectrum),
                             where=roi_norm_spectrum != 0)
        if normalise_with_shuttercount:
            average_shuttercount = self.get_shuttercount_normalised_correction_parameter()
            spectrum = spectrum / average_shuttercount
        LOG.debug("Computing spectrum: ROI=%s, Open ROI=%s, mode=%s", roi, open_beam_roi, mode.name)
        return spectrum

    def store_spectrum(self,
                       roi: SensibleROI,
                       mode: SpecType,
                       normalise_with_shuttercount: bool,
                       spectrum: np.ndarray,
                       open_beam_roi: SensibleROI | None = None) -> None:
        if open_beam_roi is None:
            open_beam_roi = roi
        params = (*roi, *open_beam_roi, mode, normalise_with_shuttercount)

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
            assert len(self._stack.shape) == 3
            return self._stack.shape[1:]
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
        csv_output.add_column("ToF_index", np.arange(self._stack.shape[0]), "Index")

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

    def save_rits_images(self,
                         directory: Path,
                         error_mode: ErrorMode,
                         binner: ROIBinner,
                         normalise: bool = False,
                         progress: Progress | None = None) -> None:
        """
        Saves multiple Region of Interest (ROI) images to RITS files.

        This method divides the ROI into multiple sub-regions defined by the binner

        Parameters:
        directory (Path): The directory where the RITS images will be saved. If None, no images will be saved.
        normalised (bool): If True, the images will be normalised.
        error_mode (ErrorMode): The error mode to use when saving the images.
        binner (ROIBinner): Binner object used to subdivide region
        normalise (bool): If True, the images will be normalised.
        progress (Progress | None): Optional progress reporter.

        Returns:
        None
        """

        x_iterations, y_iterations = binner.lengths()
        progress = Progress.ensure_instance(progress, num_steps=x_iterations * y_iterations)

        is_valid, message = binner.is_valid()
        if not is_valid:
            raise ValueError(f"Invalid binning: {message}")

        for y in range(y_iterations):
            for x in range(x_iterations):
                sub_roi = binner.get_sub_roi(x, y)
                path = directory / f"rits_image_{x}_{y}.dat"
                self.save_rits_roi(path, error_mode, sub_roi, normalise)
                progress.update()

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
                self.tof_plot_range = (0, self._stack.shape[0] - 1)
                self.tof_range = (0, self._stack.shape[0] - 1)
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

    def get_stack_length(self) -> int:
        if self._stack is not None:
            return self._stack.data.shape[0]
        else:
            return 0

    def fit_single_region(
        self,
        spectrum: np.ndarray,
        fitting_region: FittingRegion,
        tof_data: np.ndarray,
        init_params: list[float],
        bounds: list[BoundType] | None = None,
    ) -> tuple[dict[str, float], float, float]:
        fitting_slice = slice(*np.searchsorted(tof_data, (fitting_region[0], fitting_region[1])))
        xvals = tof_data[fitting_slice]
        yvals = spectrum[fitting_slice]
        return self.fitting_engine.find_best_fit(xvals, yvals, init_params, params_bounds=bounds)

    def set_fit_results(self, results: list[tuple[str, SpectrumFitResult]] | None) -> None:
        """
        Store filtered fit results to only good fits and create a lookup for building parameter maps
        """
        self.fit_results = results
        self._good_fits_by_roi_name = {
            name: result
            for name, result in results if result.is_good_fit
        } if results else {}
        LOG.info("Stored fit results")

    def get_fit_results(self) -> list[tuple[str, SpectrumFitResult]] | None:
        return self.fit_results

    def compute_chi2_threshold(self, percentile: float = 95.0) -> float | None:
        """
        Return a given percentile of good-fit rss_per_dof values, or None if unavailable.
        Acts as a good starting point to be altered based on data and preference

        @param percentile: The percentile of rss_per_dof values to return as the chi2 threshold
        @return: The chi2 threshold value or None if no valid fit results are available
        """
        if self.fit_results is None:
            return None
        valid_chi2_values = [
            result.rss_per_dof for _, result in self.fit_results
            if result.is_good_fit and np.isfinite(result.rss_per_dof) and result.rss_per_dof > 0
        ]
        return float(np.percentile(valid_chi2_values, percentile)) if valid_chi2_values else None

    def build_parameter_map(self,
                            param_name: str,
                            binner: ROIBinner,
                            chi2_threshold: float | None = None) -> np.ndarray:
        """
        Build a 2D parameter map from stored fit results for the given parameter name.

        Grid dimensions are derived from the binner sub-ROIs.
        Fits higher than chi2_threshold excluded from map.

        @param param_name: The name of the fitted parameter to map
        @param binner: The ROIBinner used when generating for fit
        @param  chi2_threshold: Optional upper bound on rss_per_dof. Exclude fits if reduced chi2 higher than threshold
        @return np.ndarray: 2D array of parameters (n_rows, n_cols) matching binner dimensions.
        """
        if self.fit_results is None:
            raise ValueError("No fit results available. Run 'Fit All' before building a parameter map.")

        n_cols, n_rows = binner.lengths()
        param_map = np.full((n_rows, n_cols), np.nan, dtype=np.float64)

        for col, row in np.ndindex(n_cols, n_rows):
            if (fit_result := self._good_fits_by_roi_name.get(binner.get_roi_name(col, row))) is None:
                continue
            if chi2_threshold is not None and fit_result.rss_per_dof > chi2_threshold:
                continue
            param_map[row, col] = fit_result.params[param_name]

        return param_map

    def calculate_colour_levels(self, map_array: np.ndarray, mode: ColourRangeMode) -> tuple[float, float]:
        """
        Handle a various outlier exclusion options to handle various distributions, falling back
        to full range if needed for IQR and percentile
        Return (lower, upper) display levels for a parameter map based on user colour range selection

        @param map_array: 2D parameter map array
        @param mode: Colour range selection
        @return: (lower, upper) tuple image display levels
        """
        finite_values = map_array[np.isfinite(map_array)]
        if finite_values.size == 0:
            return 0.0, 1.0

        strategies = {
            ColourRangeMode.IQR: self._colour_levels_iqr,
            ColourRangeMode.MAD: self._colour_levels_mad,
            ColourRangeMode.PERCENTILE: self.colour_levels_percentile,
        }
        lower, upper = strategies[mode](finite_values)

        if lower >= upper:
            return float(finite_values.min()), float(finite_values.max())
        return lower, upper

    @staticmethod
    def colour_levels_percentile(finite_values: np.ndarray) -> tuple[float, float]:
        """Return the 2nd-98th percentile range of the given finite values."""
        return float(np.percentile(finite_values, 2)), float(np.percentile(finite_values, 98))

    @staticmethod
    def _colour_levels_mad(finite_values: np.ndarray) -> tuple[float, float]:
        """Clips to median +- 3xMAD and falls back to full range when MAD = 0 to exclude outliers"""
        median = np.median(finite_values)
        mad = np.median(np.abs(finite_values - median))
        if mad == 0:
            return float(finite_values.min()), float(finite_values.max())
        return float(max(finite_values.min(), median - 3.0 * mad)), float(min(finite_values.max(), median + 3.0 * mad))

    @staticmethod
    def _colour_levels_iqr(finite_values: np.ndarray) -> tuple[float, float]:
        """Clips outliers beyond 1.5xIQR to exclude outliers"""
        lower_quartile, upper_quartile = np.percentile(finite_values, [25, 75])
        iqr = upper_quartile - lower_quartile
        return (float(max(finite_values.min(),
                          lower_quartile - 1.5 * iqr)), float(min(finite_values.max(), upper_quartile + 1.5 * iqr)))

    def build_full_sample_parameter_map(self, map_array: np.ndarray, binner: ROIBinner) -> np.ndarray:
        """
        Create array matching sample image size filled with NaN and insert parameter map over ROI region
        set by binner for overlaying over sample image.

        Each bin occupies exactly step_size pixels in both axes to avoid edge artefacts
        using bin_size which may be larger when bins overlap.

        @param map_array: parameter map
        @param binner: The binner used when generating the map
        @return: Array of shape (height, width) matching the sample stack dimensions
        """
        img_height, img_width = self.get_image_shape()
        full_map = np.full((img_height, img_width), np.nan, dtype=np.float32)
        step = binner.step_size

        n_cols, n_rows = binner.lengths()
        for col, row in np.ndindex(n_cols, n_rows):
            param_value = map_array[row, col]
            if np.isfinite(param_value):
                x_start = binner.left_indexes[col]
                x_end = min(x_start + step, img_width)
                y_start = binner.top_indexes[row]
                y_end = min(y_start + step, img_height)
                full_map[y_start:y_end, x_start:x_end] = np.float32(param_value)

        return full_map

    def save_parameter_map(self, path: Path, map_array: np.ndarray) -> None:
        """
        Save parameter map array to a TIFF file

        @param path: File path for the TIFF
        @param map_array: Parameter Map
        """
        saver.write_img(map_array, str(path))

    def load_rois_from_csv(self, path: Path):
        loaded_rois_list = []
        with open(path, encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            header = csv_reader.fieldnames
            for line in csv_reader:
                loaded_rois_list.append(line)

        assert header is not None
        assert all(field in header for field in ["X Min", "Y Min", "X Max", "Y Max"]), \
            "ROI fields not found in CSV file. Please use exported ROIs instead."

        height, width = self.get_image_shape()
        for roi_dict in loaded_rois_list:
            assert isinstance(roi_dict, dict)
            roi_name = roi_dict["ROI"]
            if roi_name != 'rits_roi' and '' not in roi_dict.values():
                roi_dict["X Min"] = 0 if float(roi_dict["X Min"]) < 0 else float(roi_dict["X Min"])
                roi_dict["Y Min"] = 0 if float(roi_dict["Y Min"]) < 0 else float(roi_dict["Y Min"])
                roi_dict["X Max"] = width if float(roi_dict["X Max"]) > width else float(roi_dict["X Max"])
                roi_dict["Y Max"] = height if float(roi_dict["Y Max"]) > height else float(roi_dict["Y Max"])
                coords = [int(float(roi_dict[field])) for field in ["X Min", "Y Min", "X Max", "Y Max"]]
                coords = [0 if coord < 0 else coord for coord in coords]
                self.presenter.do_add_roi(roi_name=roi_name, coords=coords, from_load=True)
                LOG.info(f"ROI loaded: name={roi_name}, coords=({coords})")

# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.io.csv_output import CSVOutput
from mantidimaging.core.utility.sensible_roi import SensibleROI

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.presenter import SpectrumViewerWindowPresenter


class SpecType(Enum):
    SAMPLE = 1
    OPEN = 2
    SAMPLE_NORMED = 3


class SpectrumViewerWindowModel:
    presenter: 'SpectrumViewerWindowPresenter'
    _stack: Optional[ImageStack] = None
    _normalise_stack: Optional[ImageStack] = None
    tof_range: tuple[int, int] = (0, 0)
    _roi_ranges: dict[str, SensibleROI]

    def __init__(self, presenter: 'SpectrumViewerWindowPresenter'):
        self.presenter = presenter
        self._roi_id_counter = 0
        self._roi_ranges = {}

    def roi_name_generator(self) -> str:
        """
        Returns a new Unique ID for newly created ROIs

        :return: A new unique ID
        """
        self._roi_id_counter += 1
        return f"roi_{self._roi_id_counter}"

    def get_list_of_roi_names(self) -> list[str]:
        """
        Get a list of rois available in the model
        """
        return list(self._roi_ranges.keys())

    def set_stack(self, stack: Optional[ImageStack]) -> None:
        self._stack = stack
        if stack is None:
            return
        self.tof_range = (0, stack.data.shape[0] - 1)
        height, width = self.get_image_shape()
        self.set_roi("all", SensibleROI.from_list([0, 0, width, height]))
        self.set_roi("roi", SensibleROI.from_list([0, 0, width, height]))

    def set_new_roi(self, name: str) -> None:
        """
        Sets a new ROI with the given name
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

        :param roi_name: The name of the ROI to get
        :return: The ROI with the given name
        """
        if roi_name not in self._roi_ranges.keys():
            raise KeyError(f"ROI {roi_name} does not exist")
        return self._roi_ranges[roi_name]

    def get_averaged_image(self) -> Optional['np.ndarray']:
        if self._stack is not None:
            tof_slice = slice(self.tof_range[0], self.tof_range[1] + 1)
            return self._stack.data[tof_slice].mean(axis=0)
        else:
            return None

    @staticmethod
    def get_stack_spectrum(stack: ImageStack, roi: SensibleROI):
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

    def get_image_shape(self) -> tuple[int, int]:
        if self._stack is not None:
            return self._stack.data.shape[1:]
        else:
            return 0, 0

    def can_export(self) -> bool:
        """
        Check if data is available to export
        @return: True if data is available to export and False otherwise
        """
        return self._stack is not None

    def save_csv(self, path: Path, normalized: bool) -> None:
        """
        Iterates over all ROIs and saves the spectrum for each one to a CSV file.

        :param path: The path to save the CSV file to.
        :param normalized: Whether to save the normalized spectrum.
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

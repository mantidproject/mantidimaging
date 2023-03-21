# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
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
        self._selected_row = 0
        self.default_roi_list = ["all", "roi"]

    @property
    def selected_row(self):
        return self._selected_row

    @selected_row.setter
    def selected_row(self, value):
        self._selected_row = value

    def reset_selected_row(self):
        self.selected_row = 0

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
        height, width = self.get_image_shape()
        self.set_roi(self.default_roi_list[0], SensibleROI.from_list([0, 0, width, height]))
        # Remove additional ROIs if they exist on sample change and reset
        if len(self._roi_ranges) > 1:
            self.presenter.do_remove_roi()
            self.set_roi(self.default_roi_list[1], SensibleROI.from_list([0, 0, width, height]))
        else:
            self.set_roi(self.default_roi_list[1], SensibleROI.from_list([0, 0, width, height]))
        if self.default_roi_list[1] not in self._roi_ranges.keys():
            self.set_new_roi(self.default_roi_list[1])
        self.default_roi_list[1] = list(self._roi_ranges.keys())[1]

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

    def remove_roi(self, roi_name) -> None:
        """
        Remove the selected ROI from the model

        @param roi_name: The name of the ROI to remove
        """
        if roi_name in self._roi_ranges.keys():
            if roi_name in self.default_roi_list:
                raise RuntimeError("Cannot remove the 'all' or 'roi' ROIs")
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
        @raises RuntimeError: If the ROI is 'all' or 'roi'
        """
        if old_name in self._roi_ranges.keys() and new_name not in self._roi_ranges.keys():
            if old_name == self.default_roi_list[0]:
                raise RuntimeError("Cannot rename the 'all' ROI")
            self._roi_ranges[new_name] = self._roi_ranges.pop(old_name)
            if old_name == self.default_roi_list[1]:
                self.default_roi_list[1] = new_name
        else:
            raise KeyError(f"Cannot rename {old_name} to {new_name} Available:{self._roi_ranges.keys()}")

    def remove_all_roi(self) -> None:
        """
        Remove all ROIs from the model excluding default ROIs 'all' and 'roi'
        """
        self._roi_ranges = {key: value for key, value in self._roi_ranges.items() if key in self.default_roi_list}
        self._roi_id_counter = 0  # Reset the counter to 0

# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.io.csv_output import CSVOutput
from mantidimaging.core.utility.sensible_roi import SensibleROI

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.presenter import SpectrumViewerWindowPresenter


class SpectrumViewerWindowModel:
    presenter: 'SpectrumViewerWindowPresenter'
    _stack: Optional[ImageStack] = None
    _normalise_stack: Optional[ImageStack] = None
    tof_range: tuple[int, int] = (0, 0)
    _roi_ranges: dict[str, SensibleROI] = {}
    normalised: bool = False

    def __init__(self, presenter: 'SpectrumViewerWindowPresenter'):
        self.presenter = presenter

    def set_stack(self, stack: ImageStack) -> None:
        self._stack = stack
        self.tof_range = (0, stack.data.shape[0] - 1)
        height, width = self.get_image_shape()
        self.set_roi("all", SensibleROI.from_list([0, 0, width, height]))
        self.set_roi("roi", SensibleROI.from_list([0, 0, width, height]))

    def set_normalise_stack(self, normalise_stack: ImageStack) -> None:
        self._normalise_stack = normalise_stack

    def set_roi(self, roi_name: str, roi: SensibleROI):
        self._roi_ranges[roi_name] = roi

    def get_roi(self, roi_name: str):
        return self._roi_ranges[roi_name]

    def get_averaged_image(self) -> Optional['np.ndarray']:
        if self._stack is not None:
            tof_slice = slice(self.tof_range[0], self.tof_range[1] + 1)
            return self._stack.data[tof_slice].mean(axis=0)
        else:
            return None

    def get_spectrum(self, roi_name: str) -> Optional['np.ndarray']:
        if self._stack is None:
            return None

        left, top, right, bottom = self.get_roi(roi_name)
        roi_data = self._stack.data[:, top:bottom, left:right]
        roi_spectrum = roi_data.mean(axis=(1, 2))
        if self.normalised and self._normalise_stack is not None:
            roi_norm_data = self._normalise_stack.data[:, top:bottom, left:right]
            roi_norm_spectrum = roi_norm_data.mean(axis=(1, 2))
            return np.divide(roi_spectrum,
                             roi_norm_spectrum,
                             out=np.zeros_like(roi_spectrum),
                             where=roi_norm_spectrum != 0)
        else:
            return roi_spectrum

    def get_image_shape(self) -> tuple[int, int]:
        if self._stack is not None:
            return self._stack.data.shape[1:]
        else:
            return 0, 0

    def save_csv(self, path: Path) -> None:
        if self._stack is None:
            raise ValueError("No stack selected")

        csv_output = CSVOutput()
        csv_output.add_column("tof_index", np.arange(self._stack.data.shape[0]))

        for roi_name in ("all", "roi"):
            csv_output.add_column(roi_name, self.get_spectrum(roi_name))

        with path.open("w") as outfile:
            csv_output.write(outfile)

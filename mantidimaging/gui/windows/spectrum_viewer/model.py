# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Optional

from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.sensible_roi import SensibleROI

if TYPE_CHECKING:
    import numpy as np
    from mantidimaging.gui.windows.spectrum_viewer.presenter import SpectrumViewerWindowPresenter


class SpectrumViewerWindowModel:
    presenter: 'SpectrumViewerWindowPresenter'
    _stack: Optional[ImageStack]
    _normalise_stack: Optional[ImageStack]
    tof_range: tuple[int, int] = (0, 0)
    roi_range: SensibleROI = SensibleROI()

    def __init__(self, presenter):
        self.presenter = presenter

    def set_stack(self, stack: ImageStack):
        self._stack = stack
        self.tof_range = (0, stack.data.shape[0] - 1)
        height, width = self.get_image_shape()
        self.roi_range = SensibleROI.from_list([0, 0, width, height])

    def set_normalise_stack(self, normalise_stack: ImageStack):
        self._normalise_stack = normalise_stack

    def get_averaged_image(self) -> 'np.ndarray':
        if self._stack is not None:
            tof_slice = slice(self.tof_range[0], self.tof_range[1] + 1)
            return self._stack.data[tof_slice].mean(axis=0)
        else:
            return None

    def get_spectrum(self) -> 'np.ndarray':
        if self._stack is not None:
            left, top, right, bottom = self.roi_range
            roi_data = self._stack.data[:, top:bottom, left:right]
            return roi_data.mean(axis=(1, 2))
        else:
            return None

    def get_image_shape(self) -> tuple[int, int]:
        if self._stack is not None:
            return self._stack.data.shape[1:]
        else:
            return 0, 0

# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Optional

from mantidimaging.core.data import ImageStack

if TYPE_CHECKING:
    import numpy as np
    from mantidimaging.gui.windows.spectrum_viewer.presenter import SpectrumViewerWindowPresenter


class SpectrumViewerWindowModel:
    presenter: 'SpectrumViewerWindowPresenter'
    _stack: Optional[ImageStack]
    _open_stack: Optional[ImageStack]
    tof_range: tuple[int, int] = (0, 0)

    def __init__(self, presenter):
        self.presenter = presenter

    def set_stack(self, stack: ImageStack):
        self._stack = stack
        self.tof_range = (0, stack.data.shape[0] - 1)

    def set_open_stack(self, open_stack: ImageStack):
        self._open_stack = open_stack

    def get_averaged_image(self) -> 'np.ndarray':
        if self._stack is not None:
            tof_slice = slice(self.tof_range[0], self.tof_range[1] + 1)
            return self._stack.data[tof_slice].mean(axis=0)
        else:
            return None

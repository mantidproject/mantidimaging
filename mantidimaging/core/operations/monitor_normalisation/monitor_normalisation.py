# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from functools import partial
from typing import Any, TYPE_CHECKING
from collections.abc import Callable  # Example of how to import from collections.abc

import numpy as np

from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from mantidimaging.gui.mvp_base import BaseMainWindowView
    from PyQt5.QtWidgets import QFormLayout, QWidget


def _divide_by_counts(data=None, counts=None):
    data[:] = np.true_divide(data, counts)


class MonitorNormalisation(BaseFilter):
    """Normalises the image data using the average count of a beam monitor from the
    experiment log file. This scaling operation is an alternative to ROI normalisation
    and allows to account for beam fluctuations and different exposure times of projections.

    Intended to be used on: Projections

    When: As a pre-processing step to normalise the grey value ranges of the data.
    """
    filter_name = "Monitor Normalisation"
    link_histograms = True

    @staticmethod
    def filter_func(images: ImageStack, progress=None) -> ImageStack:
        """
        :return: The ImageStack object which has been normalised.
        """
        if images.num_projections == 1:
            # we can't really compute the preview as the image stack copy
            # passed in doesn't have the logfile in it
            raise RuntimeError("No logfile available for this stack.")

        counts = images.counts()

        if counts is None:
            raise RuntimeError("No loaded log values for this stack.")

        normalization_factor = counts.value / counts.value[0]
        params = {'normalization_factor': normalization_factor}
        ps.run_compute_func(MonitorNormalisation.compute_function, images.data.shape[0], images.shared_array, params,
                            progress)
        return images

    @staticmethod
    def compute_function(i: int, array: np.ndarray, params: dict[str, np.ndarray]):
        normalization_factor = params['normalization_factor']
        array[i] /= normalization_factor

    @staticmethod
    def register_gui(form: QFormLayout, on_change: Callable, view: BaseMainWindowView) -> dict[str, QWidget]:
        return {}

    @staticmethod
    def execute_wrapper(*args) -> partial:
        return partial(MonitorNormalisation.filter_func)

    @staticmethod
    def validate_execute_kwargs(kwargs: dict[str, Any]) -> bool:
        return True

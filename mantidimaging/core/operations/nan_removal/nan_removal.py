# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numpy as np
from scipy.ndimage import median_filter

from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout, QWidget
    from mantidimaging.core.data import ImageStack
    from mantidimaging.gui.mvp_base import BaseMainWindowView
    from collections.abc import Callable


def enable_correct_fields_only(mode_field, replace_value_field):
    replace_value_field.setEnabled(mode_field.currentText() == "Constant")


class NaNRemovalFilter(BaseFilter):
    """
    Replaces the NaNs with a specified value or the median of neighbouring pixels.

    Intended to be used on: Projections

    When: To remove NaNs before reconstruction.

    Note that the median method cannot remove continuous blocks of NaNs.
    """

    filter_name = "NaN Removal"
    link_histograms = True

    MODES = ["Constant", "Median"]

    @staticmethod
    def filter_func(data, replace_value=None, mode_value="Constant", progress=None) -> ImageStack:
        """
        :param data: The input data.
        :param mode_value: Values to replace NaNs with. One of ["Constant", "Median"]
        :param replace_value: In constant mode, the value to replace NaNs with.
        :param progress: The optional Progress object.
        :return: The ImageStack object with the NaNs replaced.
        """

        if mode_value == "Constant":
            params = {'replace_value': replace_value}
            ps.run_compute_func(NaNRemovalFilter.compute_constant_function, data.data.shape[0], data.shared_array,
                                params, progress)
        elif mode_value == "Median":
            ps.run_compute_func(NaNRemovalFilter.compute_median_function, data.data.shape[0], data.shared_array, {},
                                progress)
        else:
            raise ValueError(f"Unknown mode: '{mode_value}'. Should be one of {NaNRemovalFilter.MODES}")

        return data

    @staticmethod
    def compute_constant_function(i: int, array: np.ndarray, params: dict):
        replace_value = params['replace_value']
        nan_idxs = np.isnan(array[i])
        array[i][nan_idxs] = replace_value

    @staticmethod
    def compute_median_function(i: int, array: np.ndarray, params: dict):
        array[i] = NaNRemovalFilter._nan_to_median(array[i], size=3, edgemode='reflect')

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BaseMainWindowView') -> dict[str, 'QWidget']:
        from mantidimaging.gui.utility import add_property_to_form

        value_range = (-10000000, 10000000)

        _, mode_field = add_property_to_form('Replace with',
                                             Type.CHOICE,
                                             valid_values=NaNRemovalFilter.MODES,
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Values used to replace NaNs")

        _, replace_value_field = add_property_to_form("Replacement Value",
                                                      'float',
                                                      valid_values=value_range,
                                                      form=form,
                                                      on_change=on_change,
                                                      tooltip="The value to replace the NaNs with")
        replace_value_field.setDecimals(7)

        mode_field.currentTextChanged.connect(lambda text: enable_correct_fields_only(mode_field, replace_value_field))

        return {"mode_field": mode_field, "replace_value_field": replace_value_field}

    @staticmethod
    def _nan_to_median(data: np.ndarray, size: int, edgemode: str):
        """
        Replaces NaN values in data with median, based on a kernel 'size' and 'edgemode'.
        Initially converts NaNs to -inf to avoid calculation issues, applies a median filter.
        After -inf changes back to NaNs to indicate unprocessed blocks.
        """
        nans = np.isnan(data)
        if np.any(nans):
            median_data = np.where(nans, -np.inf, data)
            median_data = median_filter(median_data, size=size, mode=edgemode)
            data = np.where(nans, median_data, data)
            if np.any(data == -np.inf):
                data = np.where(np.logical_and(nans, data == -np.inf), np.nan, data)

        return data

    @staticmethod
    def execute_wrapper(mode_field=None, replace_value_field=None):
        mode_value = mode_field.currentText()
        replace_value = replace_value_field.value()
        return partial(NaNRemovalFilter.filter_func, replace_value=replace_value, mode_value=mode_value)

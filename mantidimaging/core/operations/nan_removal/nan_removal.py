# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Dict, TYPE_CHECKING

import numpy as np
from tomopy import median_filter

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

        params = {'replace_value': replace_value, 'mode_value': mode_value}
        ps.run_compute_func(NaNRemovalFilter.compute_function, data.data.shape[0], data.shared_array, params, progress)

        return data

    @staticmethod
    def compute_function(i: int, array: np.ndarray, params: dict):
        mode_value = params['mode_value']
        replace_value = params['replace_value']
        if mode_value == "Constant":
            nan_idxs = np.isnan(array[i])
            array[i][nan_idxs] = replace_value
        elif mode_value == "Median":
            nans = np.isnan(array[i])
            if np.any(nans):
                median_data = np.where(nans, -np.inf, array[i])
                median_data = median_filter(median_data, size=3, mode='reflect')
                array[i] = np.where(nans, median_data, array[i])
                # Convert infs back to NaNs
                array[i] = np.where(np.logical_and(nans, array[i] == -np.inf), np.nan, array[i])
        else:
            raise ValueError(f"Unknown mode: '{mode_value}'. Should be one of {NaNRemovalFilter.MODES}")

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BaseMainWindowView') -> Dict[str, 'QWidget']:
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
    def execute_wrapper(mode_field=None, replace_value_field=None):
        mode_value = mode_field.currentText()
        replace_value = replace_value_field.value()
        return partial(NaNRemovalFilter.filter_func, replace_value=replace_value, mode_value=mode_value)

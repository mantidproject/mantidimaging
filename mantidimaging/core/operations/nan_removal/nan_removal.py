# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from collections.abc import Callable
from functools import partial
from logging import getLogger
from typing import Dict

import numpy as np
from PyQt5.QtWidgets import QFormLayout, QWidget
import scipy.ndimage as scipy_ndimage

from mantidimaging.core.data import ImageStack
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility.qt_helpers import Type


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
            sample = data.data
            nan_idxs = np.isnan(sample)
            sample[nan_idxs] = replace_value
        elif mode_value == "Median":
            _execute(data, 3, "reflect", progress)
        else:
            raise ValueError(f"Unknown mode: '{mode_value}'\nShould be one of {NaNRemovalFilter.MODES}")

        return data

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


def _nan_to_median(data: np.ndarray, size: int, edgemode: str):
    nans = np.isnan(data)
    if np.any(nans):
        median_data = np.where(nans, -np.inf, data)
        median_data = scipy_ndimage.median_filter(median_data, size=size, mode=edgemode)
        data = np.where(nans, median_data, data)

        if np.any(data == -np.inf):
            # Convert any left over -infs back to NaNs
            data = np.where(np.logical_and(nans, data == -np.inf), np.NaN, data)

    return data


def _execute(images: ImageStack, size, edgemode, progress=None):
    log = getLogger(__name__)
    progress = Progress.ensure_instance(progress, task_name='NaN Removal')

    # create the partial function to forward the parameters
    f = ps.create_partial(_nan_to_median, ps.return_to_self, size=size, edgemode=edgemode)

    with progress:
        log.info("PARALLEL NaN Removal filter, with pixel data type: {0}".format(images.dtype))

        ps.execute(f, [images.shared_array], images.data.shape[0], progress, msg="NaN Removal")

    return images

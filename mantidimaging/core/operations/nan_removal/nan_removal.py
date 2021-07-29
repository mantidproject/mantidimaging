# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from collections import Callable
from functools import partial
from typing import Dict

import numpy as np
from PyQt5.QtWidgets import QFormLayout, QWidget

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.gui.mvp_base import BaseMainWindowView


class NaNRemovalFilter(BaseFilter):
    """
    Replaces all NaNs in the images with a specified value.

    Intended to be used on: Projections

    When: To remove NaNs before reconstruction.
    """

    filter_name = "NaN Removal"
    link_histograms = True

    @staticmethod
    def filter_func(data: Images, replace_value: float, progress=None) -> Images:
        """
        Replaces the NaNs with a specified value.
        :param data: The input data.
        :param replace_value: The data to replace the NaNs with.
        :param progress: The optional Progress object.
        :return: The Images object with the NaNs replaced.
        """

        sample = data.data
        nan_idxs = np.isnan(sample)
        sample[nan_idxs] = replace_value

        return data

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BaseMainWindowView') -> Dict[str, 'QWidget']:
        from mantidimaging.gui.utility import add_property_to_form

        value_range = (-10000000, 10000000)

        _, replace_value_field = add_property_to_form("Replacement Value",
                                                      'float',
                                                      valid_values=value_range,
                                                      form=form,
                                                      on_change=on_change,
                                                      tooltip="The value to replace the NaNs with")
        replace_value_field.setDecimals(7)

        return {"replace_value_field": replace_value_field}

    @staticmethod
    def execute_wrapper(replace_value_field=None):
        replace_value = replace_value_field.value()
        return partial(NaNRemovalFilter.filter_func, replace_value=replace_value)

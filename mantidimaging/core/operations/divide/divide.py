# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, TYPE_CHECKING
from collections.abc import Callable

from mantidimaging import helper as h
import numpy as np

from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout, QDoubleSpinBox, QComboBox
    from mantidimaging.gui.mvp_base import BasePresenter
    from mantidimaging.core.data import ImageStack


class DivideFilter(BaseFilter):
    """Divides a stack of images by a value. That value can be the pixel size,
    and can be specified in either microns or cms, to obtain attenuation values.

    Intended to be used on: Reconstructed slices

    When: To calculate attenuation values by dividing by the pixel size in microns

    Caution: Check preview values before applying divide
    """
    filter_name = "Divide"
    link_histograms = True

    @staticmethod
    def filter_func(images: ImageStack, value: int | float = 0, unit="micron", progress=None) -> ImageStack:
        """
        :param value: The division value.
        :param unit: The unit of the divisor.

        :return: The ImageStack object which has been divided by a value.
        """
        h.check_data_stack(images)
        if not value:
            raise ValueError('value parameter must not equal 0 or None')

        if unit == "micron":
            value *= 1e-4

        params = {'value': value}
        ps.run_compute_func(DivideFilter.compute_function, images.data.shape[0], images.shared_array, params, progress)

        return images

    @staticmethod
    def compute_function(i: int, array: np.ndarray, params: dict):
        value = params['value']
        array[i] /= value

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BasePresenter') -> dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form

        _, value_widget = add_property_to_form("Divide by",
                                               Type.FLOAT,
                                               default_value=1,
                                               valid_values=[1e-7, 10000],
                                               form=form,
                                               on_change=on_change,
                                               tooltip="Value the data will be divided by")
        assert value_widget is not None, "Requested widget was for FLOAT, got None instead"
        value_widget.setDecimals(7)
        _, unit_widget = add_property_to_form("Unit",
                                              Type.CHOICE,
                                              valid_values=["micron", "cm"],
                                              form=form,
                                              on_change=on_change,
                                              tooltip="The unit of the input number. "
                                              "Microns will be converted to cm before division")

        return {'value_widget': value_widget, 'unit_widget': unit_widget}

    @staticmethod
    def execute_wrapper(  # type: ignore
            value_widget: QDoubleSpinBox, unit_widget: QComboBox) -> partial:
        value = value_widget.value()
        unit = unit_widget.currentText()
        return partial(DivideFilter.filter_func, value=value, unit=unit)

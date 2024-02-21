# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Union, Callable, Dict, Any, TYPE_CHECKING

import numpy as np
from mantidimaging.core.parallel import shared as ps
from mantidimaging import helper as h
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

    @classmethod
    def filter_func(cls, images: ImageStack, value: Union[int, float] = 0, unit="micron", progress=None) -> ImageStack:

        h.check_data_stack(images)
        if not value:
            raise ValueError('value parameter must not equal 0 or None')

        if unit == "micron":
            value *= 1e-4

        params = {'value': value}
        ps.run_compute_func(cls.compute_function, images.data, params, progress)

        return images

    def compute_function(data: np.ndarray, params: Dict[str, any], progress=None):
        value = params['value']
        num_images = data.shape[0]

        for i in range(num_images):
            data[i] /= value
            if progress is not None:
                progress.update(i / num_images)

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BasePresenter') -> Dict[str, Any]:
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

    @classmethod
    def execute_wrapper(cls, value_widget: QDoubleSpinBox, unit_widget: QComboBox) -> Callable:

        def wrapper(images: ImageStack, progress=None):
            value = value_widget.value()
            unit = unit_widget.currentText()
            return cls.filter_func(images, value=value, unit=unit, progress=progress)

        return wrapper

    @staticmethod
    def validate_execute_kwargs(kwargs: Dict[str, Any]) -> bool:
        if 'value_widget' not in kwargs:
            return False
        return True

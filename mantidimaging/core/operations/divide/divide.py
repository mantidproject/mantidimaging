# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from typing import Union, Callable, Dict, Any

from PyQt5.QtWidgets import QFormLayout, QDoubleSpinBox, QComboBox

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility.qt_helpers import Type


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
    def filter_func(images: Images, value: Union[int, float] = 0, unit="micron", progress=None) -> Images:
        h.check_data_stack(images)
        if not value:
            raise ValueError('value parameter must not equal 0 or None')

        if unit == "micron":
            value *= 1e-4

        images.data /= value
        return images

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

    @staticmethod
    def execute_wrapper(  # type: ignore
            value_widget: QDoubleSpinBox, unit_widget: QComboBox) -> partial:
        value = value_widget.value()
        unit = unit_widget.currentText()
        return partial(DivideFilter.filter_func, value=value, unit=unit)

    @staticmethod
    def validate_execute_kwargs(kwargs: Dict[str, Any]) -> bool:
        if 'value_widget' not in kwargs:
            return False
        return True

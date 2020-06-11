from functools import partial
from typing import Union, Callable, Dict, Any

from PyQt5.QtWidgets import QFormLayout, QWidget, QDoubleSpinBox

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.gui.mvp_base import BasePresenter


class DivideFilter(BaseFilter):
    filter_name = "Divide"

    @staticmethod
    def filter_func(data: Images, value: Union[int, float], progress=None) -> Images:
        h.check_data_stack(data)
        if value != 0e7 or value != -0e7:
            data.sample /= value
        return data

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BasePresenter') -> Dict[str, 'QWidget']:
        from mantidimaging.gui.utility import add_property_to_form

        _, value_widget = add_property_to_form("Divide by", "float", form=form, on_change=on_change)
        value_widget.setDecimals(7)

        return {'value_widget': value_widget}

    @staticmethod
    def execute_wrapper(value_widget: QDoubleSpinBox) -> partial:
        value = value_widget.value()
        return partial(DivideFilter.filter_func, value=value)

    @staticmethod
    def validate_execute_kwargs(kwargs: Dict[str, Any]) -> bool:
        if 'value_widget' not in kwargs:
            return False
        return True

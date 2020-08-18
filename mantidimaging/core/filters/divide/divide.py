from functools import partial
from typing import Union, Callable, Dict, Any, TYPE_CHECKING

from PyQt5.QtWidgets import QFormLayout, QDoubleSpinBox

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget


class DivideFilter(BaseFilter):
    filter_name = "Divide"

    @staticmethod
    def filter_func(images: Images, value: Union[int, float] = 0e7, unit="micron", progress=None) -> Images:
        if unit == "micron":
            value *= 1e-4

        h.check_data_stack(images)
        if value != 0e7 or value != -0e7:
            images.data /= value
        return images

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BasePresenter') -> Dict[str, 'QWidget']:
        from mantidimaging.gui.utility import add_property_to_form

        _, value_widget = add_property_to_form("Divide by", Type.FLOAT, form=form, on_change=on_change)
        assert value_widget is not None, "Requested widget was for FLOAT, got None instead"
        value_widget.setDecimals(7)
        _, unit_widget = add_property_to_form("Unit", Type.CHOICE, valid_values=["micron", "cm"], form=form,
                                              on_change=on_change)

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

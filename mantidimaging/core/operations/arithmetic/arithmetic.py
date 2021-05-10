# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from typing import Callable, Dict

from PyQt5.QtWidgets import QFormLayout, QWidget, QDoubleSpinBox

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility.qt_helpers import add_property_to_form, MAX_SPIN_BOX, Type

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter


class ArithmeticFilter(BaseFilter):
    """

    """

    filter_name = "Arithmetic"
    link_histograms = True

    @staticmethod
    def filter_func(images: Images,
                    div_val: float = 1.0,
                    mult_val: float = 1.0,
                    add_val: float = 0.0,
                    sub_val: float = 0.0,
                    progress=None) -> Images:
        """
        Apply arithmetic operations to the pixels.

        :param images: The Images object.
        :param mult_val: The multiplication value.
        :param div_val: The division value.
        :param add_val: The addition value.
        :param sub_val: The subtraction value.
        :param progress: The Progress object isn't used.
        :return: The processed Images object.
        """
        if div_val != 0:
            images.data /= div_val
        if mult_val != 0:
            images.data *= mult_val
        images.data = images.data + add_val - sub_val
        return images

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BaseMainWindowView') -> Dict[str, 'QWidget']:
        _, mult_input_widget = add_property_to_form('Multiply',
                                                    Type.FLOAT,
                                                    form=form,
                                                    on_change=on_change,
                                                    default_value=1.0,
                                                    valid_values=(-MAX_SPIN_BOX, MAX_SPIN_BOX),
                                                    tooltip="The multiplication value.")
        _, div_input_widget = add_property_to_form('Divide',
                                                   Type.FLOAT,
                                                   form=form,
                                                   on_change=on_change,
                                                   default_value=1.0,
                                                   valid_values=(-MAX_SPIN_BOX, MAX_SPIN_BOX),
                                                   tooltip="The division value.")
        _, add_input_widget = add_property_to_form('Add',
                                                   Type.FLOAT,
                                                   form=form,
                                                   on_change=on_change,
                                                   default_value=0.0,
                                                   valid_values=(-MAX_SPIN_BOX, MAX_SPIN_BOX),
                                                   tooltip="The add value.")
        _, sub_input_widget = add_property_to_form('Subtract',
                                                   Type.FLOAT,
                                                   form=form,
                                                   on_change=on_change,
                                                   default_value=0.0,
                                                   valid_values=(-MAX_SPIN_BOX, MAX_SPIN_BOX),
                                                   tooltip="The subtract value.")

        return {
            'mult_input_widget': mult_input_widget,
            'div_input_widget': div_input_widget,
            'add_input_widget': add_input_widget,
            'sub_input_widget': sub_input_widget,
        }

    @staticmethod
    def execute_wrapper(  # type: ignore
            mult_input_widget: QDoubleSpinBox, div_input_widget: QDoubleSpinBox, add_input_widget: QDoubleSpinBox,
            sub_input_widget: QDoubleSpinBox) -> partial:
        return partial(ArithmeticFilter.filter_func,
                       mult_val=mult_input_widget.value(),
                       div_val=div_input_widget.value(),
                       add_val=add_input_widget.value(),
                       sub_val=sub_input_widget.value())

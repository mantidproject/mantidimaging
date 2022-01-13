# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from functools import partial
from typing import Callable, Dict, Optional

import numpy as np
from PyQt5.QtWidgets import QFormLayout, QWidget, QDoubleSpinBox

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility.qt_helpers import add_property_to_form, MAX_SPIN_BOX, Type

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps


def _arithmetic_func(data: np.ndarray, div_val: float, mult_val: float, add_val: float, sub_val: float):
    """
    Process target function for the arithmetic operation.
    :param data: The data array.
    :param div_val: The division value.
    :param mult_val: The multiplication value.
    :param add_val: The addition value.
    :param sub_val: The subtraction value.
    """
    for i in range(len(data)):
        data[i] = data[i] / div_val * mult_val + add_val - sub_val


class ArithmeticFilter(BaseFilter):
    """Add, subtract, multiply, or divide all grey values of an image with the given values.

    Intended to be used on: Any

    When: If you want to offset or rescale an image.

    """
    filter_name = "Arithmetic"

    @staticmethod
    def filter_func(images: Images,
                    div_val: float = 1.0,
                    mult_val: float = 1.0,
                    add_val: float = 0.0,
                    sub_val: float = 0.0,
                    cores: Optional[int] = None,
                    progress=None) -> Images:
        """
        Apply arithmetic operations to the pixels.
        :param images: The Images object.
        :param mult_val: The multiplication value.
        :param div_val: The division value.
        :param add_val: The addition value.
        :param sub_val: The subtraction value.
        :param cores: The number of cores that will be used to process the data.
        :param progress: The Progress object isn't used.
        :return: The processed Images object.
        """
        if div_val == 0 or mult_val == 0:
            raise ValueError("Unable to proceed with operation because division/multiplication value is zero.")

        _execute(images.data, div_val, mult_val, add_val, sub_val, cores, progress)
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
                                                   tooltip="The add value.",
                                                   single_step_size=1e-6)
        _, sub_input_widget = add_property_to_form('Subtract',
                                                   Type.FLOAT,
                                                   form=form,
                                                   on_change=on_change,
                                                   default_value=0.0,
                                                   valid_values=(-MAX_SPIN_BOX, MAX_SPIN_BOX),
                                                   tooltip="The subtract value.",
                                                   single_step_size=1e-6)

        add_input_widget.setDecimals(6)
        sub_input_widget.setDecimals(6)

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


def _execute(data: np.ndarray, div_val: float, mult_val: float, add_val: float, sub_val: float, cores: Optional[int],
             progress):
    do_arithmetic = ps.create_partial(_arithmetic_func, fwd_function=ps.arithmetic)
    ps.shared_list = [data, div_val, mult_val, add_val, sub_val]
    ps.execute(do_arithmetic, data.shape[0], progress, cores=cores)

# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from functools import partial
from typing import TYPE_CHECKING
from collections.abc import Callable

from mantidimaging.gui.utility.qt_helpers import add_property_to_form, MAX_SPIN_BOX, Type
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps

if TYPE_CHECKING:
    import numpy as np
    from mantidimaging.gui.mvp_base import BaseMainWindowView
    from mantidimaging.core.data import ImageStack
    from PyQt5.QtWidgets import QFormLayout, QWidget, QDoubleSpinBox


class ArithmeticFilter(BaseFilter):
    """Add, subtract, multiply, or divide all grey values of an image with the given values.

    Intended to be used on: Any

    When: If you want to offset or rescale an image.

    """
    filter_name = "Arithmetic"

    @staticmethod
    def filter_func(images: ImageStack,
                    div_val: float = 1.0,
                    mult_val: float = 1.0,
                    add_val: float = 0.0,
                    sub_val: float = 0.0,
                    progress=None) -> ImageStack:
        """
        Apply arithmetic operations to the pixels.
        :param images: The ImageStack object.
        :param mult_val: The multiplication value.
        :param div_val: The division value.
        :param add_val: The addition value.
        :param sub_val: The subtraction value.
        :param progress: The Progress object isn't used.
        :return: The processed ImageStack object.
        """
        if div_val == 0 or mult_val == 0:
            raise ValueError("Unable to proceed with operation because division/multiplication value is zero.")

        params = {'div': div_val, 'mult': mult_val, 'add': add_val, 'sub': sub_val}
        ps.run_compute_func(ArithmeticFilter.compute_function, images.data.shape[0], images.shared_array, params,
                            progress)

        return images

    @staticmethod
    def compute_function(i: int, array: np.ndarray, params: dict[str, float]):
        array[i] = array[i] * (params["mult"] / params["div"]) + (params["add"] - params["sub"])

    @staticmethod
    def register_gui(form: QFormLayout, on_change: Callable, view: BaseMainWindowView) -> dict[str, QWidget]:
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

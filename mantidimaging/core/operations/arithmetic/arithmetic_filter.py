# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from typing import Callable, Dict, Type

from PyQt5.QtWidgets import QFormLayout, QWidget

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.utility.qt_helpers import add_property_to_form, MAX_SPIN_BOX

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter


class ArithmeticFilter(BaseFilter):

    filter_name = "Arithmetic"
    link_histograms = True

    @staticmethod
    def filter_func(images: Images, mult_val: float = 1.0, add_val: float = 1.0) -> Images:
        images.data *= mult_val
        images.data += add_val
        return images

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BaseMainWindowView') -> Dict[str, 'QWidget']:
        _, mult_input_widget = add_property_to_form('Multiply',
                                                    Type.FLOAT,
                                                    form=form,
                                                    on_change=on_change,
                                                    valid_values=(-MAX_SPIN_BOX, MAX_SPIN_BOX),
                                                    tooltip="The multiplication value.")
        _, add_input_widget = add_property_to_form('Add',
                                                   Type.FLOAT,
                                                   form=form,
                                                   on_change=on_change,
                                                   valid_values=(-MAX_SPIN_BOX, MAX_SPIN_BOX),
                                                   tooltip="The add value.")

    @staticmethod
    def execute_wrapper(args) -> partial:
        pass
